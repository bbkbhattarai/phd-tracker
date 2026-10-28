#!/usr/bin/env python3
"""Vacancy-first collector v2.9 with multi-profile matching. No synthetic opportunities. Missing deadlines stay unverified.
Runs in GitHub Actions; archives source-health and previously discovered records.
"""
import datetime as dt
from email.utils import parsedate_to_datetime
import hashlib
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
TODAY=dt.datetime.now(dt.timezone.utc).date()
SESSION=requests.Session()
SESSION.headers.update({'User-Agent':'PhDRadarResearchMonitor/2.0 (+public research opportunity discovery; no login; contact repository owner)','Accept':'text/html,application/xhtml+xml'})
TIMEOUT=18
MAX_ARCHIVE_PAGES=45
# The browser stores draft search terms locally. Only the version committed to
# scripts/search_terms.json affects scheduled GitHub Actions searches.
SEARCH_TERMS_FILE = ROOT / 'scripts/search_terms.json'
DEFAULT_TOPICS = ['hearing', 'auditory', 'audiology', 'cochlear implant', 'psychoacoustics']

def validate_terms(data):
    result = {}
    for key in ('include_phrases', 'exclude_phrases'):
        value = data.get(key, [])
        if not isinstance(value, list):
            raise ValueError(f'{key} must be an array')
        phrases = []
        for raw in value:
            if not isinstance(raw, str):
                raise ValueError(f'{key} can contain only strings')
            item = re.sub(r'\s+', ' ', raw.strip())
            if not item or len(item) > 100:
                continue
            if item.casefold() not in [x.casefold() for x in phrases]:
                phrases.append(item)
        if len(phrases) > 80:
            raise ValueError(f'{key} cannot contain over 80 phrases')
        result[key] = phrases
    if not result['include_phrases']:
        raise ValueError('At least one research search phrase is required')
    return result

def phrase_pattern(phrases):
    # Literal user phrases, never executable regex patterns.
    pieces = []
    for phrase in sorted(phrases, key=len, reverse=True):
        escaped = re.escape(phrase).replace(r'\ ', r'\s+')
        pieces.append(r'(?<!\w)' + escaped + r'(?!\w)')
    return re.compile('|'.join(pieces), re.I)

SEARCH_TERMS = validate_terms(json.loads(SEARCH_TERMS_FILE.read_text(encoding='utf-8'))) if SEARCH_TERMS_FILE.exists() else {'include_phrases': DEFAULT_TOPICS, 'exclude_phrases': []}
# Search profiles are GitHub-synced settings. Every recorded match is explicitly
# grounded in a literal phrase; no semantic matching is fabricated.
PROFILES_FILE=ROOT/'scripts/search_profiles.json'
LEVELS=('focused','balanced','exploratory')
REGIONS=('UK','Scotland','Europe','USA','Canada','Australia','New Zealand','Hong Kong','Asia')
CATEGORIES=('advertised_phd','lab_recruiting')

def validate_profiles(data):
    if not isinstance(data,dict) or not isinstance(data.get('profiles'),list):
        raise ValueError('search_profiles.json must contain profiles array')
    if len(data['profiles'])>12:raise ValueError('Maximum 12 profiles')
    out=[];seen=set()
    for raw in data['profiles']:
        if not isinstance(raw,dict):raise ValueError('Invalid profile')
        profile_id=raw.get('id')
        if not isinstance(profile_id,str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,49}',profile_id):raise ValueError('Invalid profile ID')
        if profile_id in seen:raise ValueError('Duplicate profile ID')
        seen.add(profile_id)
        name=raw.get('name','')
        if not isinstance(name,str) or not (1<=len(name.strip())<=80):raise ValueError('Invalid profile name')
        level=raw.get('match_level','focused')
        if level not in LEVELS:raise ValueError('Unknown search level')
        fields={}
        for key in ('core_phrases','related_phrases','exploratory_phrases','exclude_phrases'):
            value=raw.get(key,[])
            if not isinstance(value,list):raise ValueError(key+' must be an array')
            fields[key]=validate_terms({'include_phrases':value or ['placeholder'], 'exclude_phrases':[]})['include_phrases'] if value else []
            if any(not isinstance(x,str) for x in value):raise ValueError(key+' requires strings')
        cats=raw.get('categories',list(CATEGORIES));regs=raw.get('regions',[])
        if not isinstance(cats,list) or not cats or any(x not in CATEGORIES for x in cats):raise ValueError('Invalid categories')
        if not isinstance(regs,list) or any(x not in REGIONS for x in regs):raise ValueError('Invalid regions')
        if raw.get('enabled',False) and not fields['core_phrases']:raise ValueError('Enabled profile needs core phrases')
        out.append({'id':profile_id,'name':name.strip(),'enabled':bool(raw.get('enabled',False)),
          'match_level':level,'regions':list(dict.fromkeys(regs)),'categories':list(dict.fromkeys(cats)),**fields})
    if not any(p['enabled'] for p in out):raise ValueError('Enable at least one profile')
    return {'schema_version':1,'profiles':out}

if PROFILES_FILE.exists():
    SEARCH_PROFILES=validate_profiles(json.loads(PROFILES_FILE.read_text(encoding='utf-8')))
else:
    SEARCH_PROFILES=validate_profiles({'profiles':[{'id':'legacy','name':'Imported phrases',
        'enabled':True,'core_phrases':SEARCH_TERMS['include_phrases'],
        'exclude_phrases':SEARCH_TERMS['exclude_phrases']}]})

def level_phrases(p):
    keys=['core_phrases']
    if p['match_level'] in ('balanced','exploratory'):keys.append('related_phrases')
    if p['match_level']=='exploratory':keys.append('exploratory_phrases')
    return [x for k in keys for x in p[k]]

def match_profiles(text, category, found_region):
    matched=[]
    for p in SEARCH_PROFILES['profiles']:
        if not p['enabled'] or category not in p['categories']:continue
        if p['regions'] and found_region!='Unspecified' and not (
            found_region in p['regions'] or (found_region=='Scotland' and 'UK' in p['regions'])):continue
        if p['exclude_phrases'] and phrase_pattern(p['exclude_phrases']).search(text):continue
        for tier,score in (('core_phrases',100),('related_phrases',70),('exploratory_phrases',40)):
            if tier=='related_phrases' and p['match_level']=='focused':continue
            if tier=='exploratory_phrases' and p['match_level']!='exploratory':continue
            items=p[tier]
            if not items:continue
            found=phrase_pattern(items).search(text)
            if found:
                matched.append({'id':p['id'],'name':p['name'],'tier':tier.replace('_phrases',''),
                    'matched_phrase':found.group(0), 'score':score})
                break
    return matched

ACTIVE_PHRASES=[term for p in SEARCH_PROFILES['profiles'] if p['enabled'] for term in level_phrases(p)]
HEARING=phrase_pattern(ACTIVE_PHRASES)
OMIT_TOPICS=None  # Exclusions apply per profile, never globally across all profiles.

PHD=re.compile(r'\b(ph\.?d\.?|d\.?phil\.?|doctoral|doctorate|studentship|graduate student|research student)\b',re.I)
EXCLUDE=re.compile(r'\b(postdoc(?:toral)?|research fellow|faculty position|assistant professor|masters? degree|MSc|AuD only)\b',re.I)
CLOSED_LAB=re.compile(r'\b(?:there are currently no open positions|no (?:current|open|available) (?:phd|doctoral|graduate|student|research) positions|not (?:currently )?(?:accepting|recruiting) (?:new )?(?:phd|graduate|doctoral) students)\b',re.I)
RECRUIT=re.compile(r'\b(apply|applications? (?:are )?(?:open|invited|welcome)|applications? (?:close|are closing|due)|recruiting|seeking|looking for|studentship|funded position|graduate assistantship|doctoral researcher|join (?:the|our) lab|prospective students?|available position|positions? are available|accepting ph\.?d\.? students?|closing date|application deadline)\b',re.I)

COUNTRY_PATTERNS=[('Hong Kong',r'\bHong Kong\b'),('New Zealand',r'\bNew Zealand\b'),('Australia',r'\bAustralia\b'),('Canada',r'\bCanada\b'),('USA',r'\b(?:USA|United States|U\.S\.A\.|US university|Texas|Illinois|Indiana|California|Maryland|New York|Massachusetts|Pittsburgh|Vanderbilt|Northwestern|Chicago|Dallas|UConn|Duke|UT Dallas|UIC)\b'),('UK',r'\b(?:United Kingdom|\bUK\b|England|Scotland|Wales|Northern Ireland|Southampton|Leicester|Edinburgh|London|Nottingham|Manchester|Sheffield|Birmingham|Bristol|Oxford|Cambridge)\b'),('Europe',r'\b(?:Germany|Netherlands|Denmark|Sweden|Norway|Finland|Belgium|France|Spain|Italy|Austria|Switzerland|Portugal|Ireland|Göttingen|Oldenburg|Leuven|Ghent|Lyon|Brussels)\b'),('Asia',r'\b(?:Singapore|Japan|China|India|South Korea|Taiwan|Malaysia|Nepal)\b')]
MONTHS='January February March April May June July August September October November December'.split()
MONTH_TOKEN='(?:'+'|'.join(MONTHS)+'|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)'
DATE_RX=re.compile(r'\b(?:\d{1,2}(?:st|nd|rd|th)?\s+'+MONTH_TOKEN+r'\s+20\d{2}|'+MONTH_TOKEN+r'\s+\d{1,2}(?:st|nd|rd|th)?,?\s+20\d{2}|20\d{2}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]20\d{2})\b',re.I)
DEADLINE_RX=re.compile(r'(?:application (?:deadline|closing date)|closing date(?: for applications)?|final date for applications|deadline(?: for application)?|apply by|applications? (?:close|due)|expressions? of interest.*?(?:by|before))\s*(?:is|:|\-|on|by|at|the)?\s*(.{0,125})',re.I)
# A deadline may occur after intermediary time/date text, but only in a short neighbourhood.


def parse_date(s,source_region='Unspecified'):
    s=re.sub(r'(\d{1,2})(?:st|nd|rd|th)\b',r'\1',s.strip(),flags=re.I).replace(',','')
    # Deliberately do not guess DD/MM versus MM/DD for unspecified locations.
    formats=['%d %B %Y','%B %d %Y','%d %b %Y','%b %d %Y','%Y-%m-%d']
    if source_region in ('UK','Europe','Australia','New Zealand','Hong Kong','Asia','Canada'):
        formats+=['%d/%m/%Y','%d-%m-%Y']
    elif source_region=='USA':
        formats+=['%m/%d/%Y','%m-%d-%Y']
    for fmt in formats:
        try:return dt.datetime.strptime(s,fmt).date()
        except ValueError:pass
    return None

def deadline(text,source_region='Unspecified'):
    found=[]
    for match in DEADLINE_RX.finditer(text[:22000]):
        for d in DATE_RX.finditer(match.group(1)):
            parsed=parse_date(d.group(0),source_region)
            if parsed:found.append(parsed)
            break
    # Earliest closing date is safer where application instructions disagree.
    return min(found).isoformat() if found else None

def fallback_findaphd_date(text):
    # FindAPhD project pages often display dates next to the institution, without the word deadline.
    for match in DATE_RX.finditer(text[:1100]):
        date=parse_date(match.group(0))
        if date and date.year>=TODAY.year and date<=TODAY+dt.timedelta(days=730):
            return date.isoformat()
    return None

def funding(text):
    t=text.lower()
    if re.search(r'\bself[- ]funded|self[- ]funding\b',t):return 'Self-funded / funding not guaranteed'
    if re.search(r'fully funded|tuition (?:fees? )?(?:covered|waived)|stipend (?:and|plus) (?:tuition|fees)',t):return 'Funding described (verify eligibility)'
    if re.search(r'competition funded|competitive funding',t):return 'Competition-funded'
    # This EURAXESS field does NOT mean a doctoral position is unfunded.
    t=re.sub(r'(?:not funded by (?:an? )?(?:eu|european|horizon)[^.]{0,65}|is (?:it|the job) funded through [^?]{0,90}\?)',' ',t)
    if re.search(r'\b(?:scholarship|assistantship|stipend|salary|funding (?:provided|available)|funding sources|funded (?:phd|doctoral|studentship|position))\b',t):return 'Funding mentioned (details unverified)'
    return 'Not specified'

def region(text,default='Unspecified'):
    for label,pattern in COUNTRY_PATTERNS:
        if re.search(pattern,text,re.I):return label
    return default

def stable_id(url):
    canon=urldefrag(url)[0].split('?')[0].rstrip('/').lower()
    return hashlib.sha256(canon.encode()).hexdigest()[:20]

def fetch(url):
    r=SESSION.get(url,timeout=TIMEOUT,allow_redirects=True)
    r.raise_for_status()
    if 'html' not in r.headers.get('content-type','text/html').lower():raise ValueError('not HTML')
    return r.text,r.url

def is_findaphd_project(url):
    p=urlparse(url)
    return p.hostname and p.hostname.endswith('findaphd.com') and bool(re.search(r'/phds/project/|/phds/project-?',p.path,re.I))

def extract_findaphd_links(html,base):
    soup=BeautifulSoup(html,'html.parser')
    result={}
    for a in soup.select('a[href]'):
        url=urljoin(base,a['href'])
        if not is_findaphd_project(url):continue
        title=a.get_text(' ',strip=True)
        container=a.find_parent(['article','li','section','div'])
        context=container.get_text(' ',strip=True)[:1800] if container else title
        if len(title)<12:
            heading=container.find(['h2','h3','h4']) if container else None
            title=heading.get_text(' ',strip=True) if heading else title
        if len(title)<12:continue
        key=stable_id(url)
        if key not in result or len(context)>len(result[key]['summary']):
            result[key]={'url':url,'title':title[:240],'summary':context[:1400]}
    return list(result.values())

def institution_links(html,base,adapter):
    """Follow only individual project advertisements on supported public index pages.
    Never equate a generic degree programme or the index itself with a vacancy.
    """
    soup=BeautifulSoup(html,'html.parser')
    links={}
    basehost=urlparse(base).hostname
    for a in soup.select('a[href]'):
        url=urljoin(base,a.get('href',''))
        parsed=urlparse(url)
        if parsed.hostname!=basehost and adapter!='baa_phd':continue
        path=parsed.path.lower()
        label=a.get_text(' ',strip=True)
        parent=a.find_parent(['article','li','section','div'])
        block=parent.get_text(' ',strip=True)[:750] if parent else label
        heading=parent.find(['h2','h3','h4']) if parent else None
        title=heading.get_text(' ',strip=True) if heading else label
        slug=(path+' '+title+' '+label).lower()
        if adapter=='bcbl_jobs':
            if not ('phd-position-' in path or 'phd_' in path):continue
        elif adapter=='ucl_studentships':
            if not ('/phd-studentships/' in path and HEARING.search(slug)):
                continue
        elif adapter=='southampton_projects':
            if not ('/study/postgraduate-research/projects/' in path and HEARING.search(title+' '+label)):
                continue
        elif adapter=='macquarie_scholarships':
            if not ('/scholarship-search/' in path and HEARING.search(slug)):
                continue
        elif adapter=='nottingham_studentships':
            # Restrict to the official job-detail links; do not import a general jobs board.
            if not ('vacancy.aspx' in path and (PHD.search(title+' '+label) or re.search(r'phd|studentship',block,re.I))):continue
        elif adapter=='baa_phd':
            # BAA keeps archived projects indefinitely. Only individual doctoral links,
            # never the BAA directory itself, are candidates for original-page verification.
            if not (re.search(r'phd|studentship',title+' '+label+' '+url,re.I) or (HEARING.search(title+' '+label) and 'findaphd.com' in parsed.netloc)):continue
            if not parsed.scheme in ('https','http'):continue
        elif adapter=='postgraduate_funding':
            # A doctoral-only funding index; individual pages use /opportunity/<slug>/<id>.
            # Advertisements must match a selected research phrase in their own card,
            # not merely anywhere in the index page or site navigation.
            if not re.fullmatch(r'/opportunity/[^/]+/\d+/?', path):continue
            if not HEARING.search(title+' '+label+' '+block):continue
        elif adapter=='strathclyde_projects':
            if not ('/postgraduateresearchphdopportunities/' in path and path.rstrip('/')!='/studywithus/postgraduateresearchphdopportunities'):continue
            if not HEARING.search(slug):continue
        else:continue
        if not HEARING.search(slug+' '+block):continue
        if not (PHD.search(slug+' '+block) or adapter in ('macquarie_scholarships','southampton_projects','strathclyde_projects','postgraduate_funding')):continue
        if len(title)<12 or title.lower() in ('more information','read more','apply now'):
            title=label if len(label)>12 else path.rstrip('/').split('/')[-1].replace('-',' ').title()
        key=stable_id(url)
        links[key]={'url':url,'title':title[:220],'summary':block[:500]}
    return list(links.values())

def classify(title,content,origin='listing',fallback='Unspecified',is_findaphd=False):
    text=(title+' '+content).strip()
    short=text[:18000]
    if EXCLUDE.search(title):return None,'non-doctoral role'
    if not HEARING.search(short):return None,'no configured research phrase matched'
    if not PHD.search(short):return None,'not doctoral'
    if origin=='lab' and CLOSED_LAB.search(short):return None,'lab explicitly reports no open positions'
    if origin!='lab' and re.search(r'\b(?:applications? (?:are )?closed|this position has been filled|studentship (?:is )?closed)\b',short[:3500],re.I):return None,'vacancy explicitly closed'
    if not RECRUIT.search(short):return None,'no recruitment evidence'
    dl=deadline(short,fallback) or (fallback_findaphd_date(short) if is_findaphd else None)
    if dl and dl<TODAY.isoformat():return None,'deadline passed'
    if origin=='lab':
        category='lab_recruiting'
        # Require stronger explicit phrasing for labs, not simply a generic graduate study page.
        if not re.search(r'\b(recruiting|seeking|looking for|positions? (?:are )?available|join (?:the|our) lab|accepting (?:new )?(?:graduate|phd)|graduate students? (?:are )?welcome|currently recruiting|currently emphasizing recruitment|open to consider applications from prospective ph\.?d\.? students|ph\.?d\.? students?\b.{0,45}currently recruiting)\b',short,re.I):
            return None,'no explicit lab recruitment'
    else: category='advertised_phd'
    matches=match_profiles(short[:9500],category,fallback if fallback not in ('Unspecified','Worldwide') else region(short))
    if not matches:return None,'not matched by an enabled search profile'
    status='deadline_verified' if dl else 'review_required'
    # Lab research grants are not proof a graduate student has funded support.
    fund=funding(short) if origin!='lab' else ('Student funding mentioned; verify terms' if re.search(r'(?:ph\.?d\.?|graduate (?:student|assistant)).{0,80}(?:funded|funding|stipend|scholarship|assistantship)',short,re.I) else 'Student funding not confirmed')
    return {'category':category,'deadline':dl,'funding':fund,'region':fallback if fallback not in ('Unspecified','Worldwide') else region(short),'verification':status,'summary':re.sub(r'\s+',' ',content)[:700],
            'profile_matches':matches,'relevance_score':max(m['score'] for m in matches)},None


# The research-list archive is independent of FindAPhD and has public, individually
# dated announcements. It is an *additional* discovery route, not a FindAPhD bypass.
ARCHIVE_TITLE=re.compile(r'(?i)\b(ph\.?d\.?|doctoral|studentship|graduate trainee|graduate student|research assistantship)\b')
ARCHIVE_DROP=re.compile(r'(?i)\b(canceled|cancelled|call for papers|conference|symposium|webinar|survey|faculty position|assistant professor|postdoc(?:toral)? only|MSc only)\b')
POST_DATE=re.compile(r'\bDate:\s*((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),?[^\n]{12,95})',re.I)
INTAKE_RX=re.compile(r'\b(?:start(?:ing)?|enter(?:ing)?|intake|join(?:ing)?|for|in)\s+(?:in\s+)?(?:the\s+)?(Fall|Spring|Autumn|Summer)\s+(20\d{2})\b',re.I)
BARE_DEADLINE=re.compile(r'\b(?:apply by|applications due|application deadline|deadline is|deadline:)\s*(?:on )?(?:by )?(?:\d{1,2}[:.]\d{2}\s*(?:am|pm)?(?:\s*\([^)]*\))?[, ]*)?(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?[, ]*((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2})(?![, ]*\d{4})',re.I)


def archive_links(html,base):
    soup=BeautifulSoup(html,'html.parser')
    candidates={}
    for a in soup.select('a[href]'):
        url=urljoin(base,a['href'])
        if not (re.search(r'/mhonarc/20\d{2}/msg\d+\.html$',urlparse(url).path) or re.search(r'/postings/20\d{2}/\d+\.html$',urlparse(url).path)):continue
        title=a.get_text(' ',strip=True)
        if not ARCHIVE_TITLE.search(title) or ARCHIVE_DROP.search(title):continue
        candidates[stable_id(url)]={'url':url,'title':re.sub(r'^\[AUDITORY\]\s*','',title,flags=re.I)}
    # MHonArc threads are approximately chronological; newest entries usually last.
    return list(candidates.values())[::-1]


def archive_post(html, fallback_title=''):
    soup=BeautifulSoup(html,'html.parser')
    heading=soup.find('h1')
    title=heading.get_text(' ',strip=True) if heading else fallback_title
    # Identify date in the message header rather than from a prospective start date.
    raw=soup.get_text('\n',strip=True)
    posted=None
    match=POST_DATE.search(raw[:7500])
    if match:
        try:posted=parsedate_to_datetime(match.group(1).strip()).date()
        except (ValueError,TypeError,IndexError):pass
    # Typical MHonArc pages divide navigation, mail headers, body, and footer by HR.
    chunks=[]
    for node in soup.select('pre,blockquote,article,main'):
        text=node.get_text(' ',strip=True)
        if len(text)>90 and not any(x in text[:100].lower() for x in ('dkim-signature:','arc-message-signature:')):
            chunks.append(text)
    if chunks:
        body=max(chunks,key=lambda x:len(x) if len(x)<15000 else 0)
        if len(body)<140:body=raw
    else:
        # Fallback for archived posts with paragraphs instead of <pre>.
        boundaries=re.split(r'\bThread-topic:[^\n]*|\bSender: AUDITORY[^\n]*',raw,flags=re.I)
        body=boundaries[-1] if len(boundaries)>1 else raw
    body=re.split(r'\bPrev by Date:|\bPrevious by thread:|\bIndex\(es\):',body)[0]
    body=re.sub(r'\s+',' ',body).strip()
    return title,body,posted


def extraction_details(text):
    intake=INTAKE_RX.search(text)
    supervisor=re.search(r'\b(?:Dr\.?|Professor|Prof\.?)\s+([A-Z][A-Za-zÀ-ÿ\-]+(?:\s+[A-Z][A-Za-zÀ-ÿ\-]+){1,2})',text)
    no_year=BARE_DEADLINE.search(text)
    return {'intake':(intake.group(1).capitalize()+' '+intake.group(2)) if intake else None,
            'supervisor':('Dr '+supervisor.group(1)) if supervisor else None,
            'deadline_note':('Apply by '+no_year.group(1)+' (year not specified; verify on source)') if no_year else None}


def excerpt(text):
    # Prefer an actionable recruiting statement, not a site's About-us paragraph.
    for rx in (r'\b(?:recruiting|seeking|accepting)\s+.{0,100}(?:PhD|doctoral|graduate)\s+students?.{0,170}',
               r'\b(?:PhD\s+(?:openings?|opportunities?|studentships?)|doctoral\s+positions?|research assistants?)[^.\n]{15,250}',
               r'\b(?:application deadline|apply by|graduate students)[^.\n]{15,250}'):
        m=re.search(rx,text,re.I)
        if m:return re.sub(r'\s+',' ',m.group(0)).strip()[:300]
    return re.sub(r'\s+',' ',text).strip()[:280]

def check_candidate(item,source,kind='listing'):
    url=item['url']
    # Get the actual advert, never substitute an article/headline result.
    html,final=fetch(url)
    soup=BeautifulSoup(html,'html.parser')
    for x in soup(['script','style','nav','footer','header']):x.decompose()
    main=soup.find('main') or soup.find('article') or soup
    body=main.get_text(' ',strip=True)[:20000]
    title=item.get('title') or source.get('title') or (soup.title.get_text(' ',strip=True) if soup.title else '')
    if not title:title=(main.find('h1').get_text(' ',strip=True) if main.find('h1') else url)
    if source.get('adapter') == 'postgraduate_funding' and not re.search(
        r'\b(?:PhD studentship|doctoral studentship|funded PhD|PhD project|PhD position|doctoral researcher|PhD scholarship|PhD research assistantship)\b',
        title+' '+body[:1900], re.I):
        return None, 'generic degree promotion or funding page'
    detail,why=classify(title,body,'lab' if kind=='lab' else 'listing',source.get('region','Unspecified'),is_findaphd_project(final))
    if not detail:return None,why
    detail.update({'fit_note':source.get('fit_note'), 'id':stable_id(final),'title':title[:230],'url':final,'source':source['name'],'last_checked':TODAY.isoformat(),'first_seen':TODAY.isoformat(),'evidence':'Original institutional page checked; always confirm status and funding with the university', 'recruitment_evidence':excerpt(body),**extraction_details(body)})
    if re.search(r'\b(?:domestic (?:applicants|students|only)|domestic applicants only|UK students only|home (?:students|applicants) only)\b',body,re.I):
        detail['eligibility_note']='Domestic/home applicants only: check eligibility'
    elif re.search(r'\b(?:domestic,? international|domestic and international|home and international students|international applicants (?:are )?(?:welcome|eligible))\b',body,re.I):
        detail['eligibility_note']='International applicants mentioned: verify funding eligibility'
    stipend=re.search(r'(?:\$|£|€)\s*[\d,.]+\s*(?:p\.?a\.?|per annum|annually|a year|gross annual salary)?',body,re.I)
    if stipend: detail['funding_note']=stipend.group(0)[:90]
    if kind=='lab':detail['verification']='recruitment_claim_needs_confirmation'
    return detail,None

def run():
    config=json.loads((ROOT/'scripts/sources.json').read_text())
    feedfile=ROOT/'data/opportunities.json'
    prior=json.loads(feedfile.read_text()) if feedfile.exists() else {}
    previous={x['id']:x for x in prior.get('opportunities',[])+prior.get('review_queue',[]) if x.get('id')}
    accepted={}; review={}; health=[]; rejected={}; errors=[]; verified_closed=set()
    def reject(why):rejected[why]=rejected.get(why,0)+1
    # listing extractor: each source's search page is parsed for actual individual projects
    for source in config['listing_sources']:
        found=0; checked=0; state='ok'; detail=''
        try:
            html,real=fetch(source['url'])
            links=extract_findaphd_links(html,real) if source['adapter']=='findaphd' else []
            found=len(links)
            if not links:state='no_projects_parsed';detail='No project links extracted. Layout or access may have changed.'
            for item in links[:35]:
                checked+=1
                try:
                    rec,why=check_candidate(item,source)
                    if rec:
                        old=previous.get(rec['id'],{})
                        rec['first_seen']=old.get('first_seen',rec['first_seen'])
                        (accepted if rec['verification']=='deadline_verified' else review)[rec['id']]=rec
                    else:reject(why)
                except Exception as e:
                    errors.append({'source':source['name'],'url':item['url'],'error':str(e)[:140]})
                time.sleep(0.12)
        except Exception as e:state='error';detail=str(e)[:200]
        health.append({'source':source['name'],'status':state,'found':found,'checked':checked,'message':detail})
    # Direct research vacancy indexes from institutional sites. No general articles,
    # degree-directory pages or third-party crawler workarounds.
    for source in config.get('institution_indexes',[]):
        found=checked=0;state='ok';message=''
        try:
            html,real=fetch(source['url'])
            links=institution_links(html,real,source['adapter'])
            found=len(links)
            if not links:
                state='no_vacancies_parsed';message='No relevant project links found; check institution page structure'
            for item in links[:min(25,int(source.get('max_links',12)))]:
                checked+=1
                try:
                    rec,why=check_candidate(item,source)
                    if rec:
                        old=previous.get(rec['id'],{})
                        rec['first_seen']=old.get('first_seen',rec['first_seen'])
                        (accepted if rec['verification']=='deadline_verified' else review)[rec['id']]=rec
                    else:reject(why)
                except Exception as e:
                    errors.append({'source':source['name'],'url':item['url'],'error':str(e)[:180]})
                time.sleep(0.08)
        except Exception as e:state='error';message=str(e)[:190]
        health.append({'source':source['name'],'status':state,'found':found,'checked':checked,'message':message})
    # Direct doctoral vacancy pages published by the original institutions.
    for source in config.get('direct_vacancies',[]):
        try:
            rec,why=check_candidate({'url':source['url'],'title':source.get('title',source['name'])},source)
            if rec:
                old=previous.get(rec['id'],{})
                rec['first_seen']=old.get('first_seen',rec['first_seen'])
                (accepted if rec['verification']=='deadline_verified' else review)[rec['id']]=rec
                health.append({'source':source['name'],'status':'verified' if rec['verification']=='deadline_verified' else 'review_lead','found':1,'checked':1})
            else:
                reject(why)
                health.append({'source':source['name'],'status':'no_current_vacancy','found':0,'checked':1,'message':why})
        except Exception as e:
            health.append({'source':source['name'],'status':'error','found':0,'checked':0,'message':str(e)[:180]})
    # UK professional bodies, grant programmes, and broader university research pages.
    # These are monitored for reachability and page changes. They DO NOT become
    # PhD opportunities because a grant or old university programme contains 'PhD'.
    previous_health={h.get('source'):h for h in prior.get('source_health',[])}
    for source in config.get('monitor_only_sources',[]):
        try:
            html,real=fetch(source['url'])
            soup=BeautifulSoup(html,'html.parser')
            for el in soup(['script','style','header','footer','nav']):el.decompose()
            main=soup.find('main') or soup
            body=re.sub(r'\s+',' ',main.get_text(' ',strip=True))[:45000]
            digest=hashlib.sha256(body.encode('utf-8')).hexdigest()[:16]
            earlier=previous_health.get(source['name'],{}).get('fingerprint')
            state='watch_changed' if earlier and earlier!=digest else 'watch_checked'
            health.append({'source':source['name'],'status':state,'found':0,'checked':1,
                'fingerprint':digest,'url':real,'source_type':source['type'],
                'message': ('Content changed since last check. Review source for a real PhD vacancy. ' if state=='watch_changed' else '')+
                           'Monitoring only: '+source.get('note','Not a verified doctoral advertisement')})
        except Exception as exc:
            health.append({'source':source['name'],'status':'error','found':0,'checked':0,
                'source_type':source['type'],'message':str(exc)[:180]})
    # AUDITORY mailing-list recruitment announcements. Reject news/events, skip
    # old announcements, and avoid declaring an advert open without evidence.
    for source in config.get('announcement_sources',[]):
        found=checked=0;status='ok';message=''
        try:
            used_url=source['url']
            try:
                html,base=fetch(used_url)
                candidates=archive_links(html,base)
                if not candidates:raise ValueError('Primary archive yielded no recruitment links')
            except Exception as primary_error:
                if not source.get('alternate_url'):raise
                used_url=source['alternate_url']
                html,base=fetch(used_url)
                candidates=archive_links(html,base)
                message='Primary archive unavailable; using alternate public archive ('+str(primary_error)[:75]+')'
            found=len(candidates)
            age_limit=int(source.get('max_age_days',150))
            max_items=min(int(source.get('max_items',45)),MAX_ARCHIVE_PAGES)
            for item in candidates[:max_items]:
                try:
                    page,real=fetch(item['url']);checked+=1
                    title,body,posted=archive_post(page,item['title'])
                    if not posted:
                        reject('announcement date missing');continue
                    if posted>TODAY+dt.timedelta(days=2) or (TODAY-posted).days>age_limit:
                        reject('old announcement');continue
                    if not ARCHIVE_TITLE.search(title) or ARCHIVE_DROP.search(title):
                        reject('not a doctoral recruitment notice');continue
                    # Exclude pages dominated by mail headers and insufficient recruitment text.
                    detail,why=classify(title,body,'listing',source.get('region','Unspecified'))
                    if not detail:
                        reject(why);continue
                    rec={**detail,'id':stable_id(real),'title':re.sub(r'^\[AUDITORY\]\s*','',title,flags=re.I)[:230],
                         'url':real,'source':source['name'],'first_seen':TODAY.isoformat(),
                         'last_checked':TODAY.isoformat(),'posted_at':posted.isoformat(),
                         'evidence':'Recruitment statement from a dated AUDITORY announcement; verify current availability with the institution',
                         'recruitment_evidence':excerpt(body),**extraction_details(body)}
                    old=previous.get(rec['id'],{})
                    rec['first_seen']=old.get('first_seen',rec['first_seen'])
                    (accepted if rec['verification']=='deadline_verified' else review)[rec['id']]=rec
                except Exception as e:
                    errors.append({'source':source['name'],'url':item['url'],'error':str(e)[:160]})
                time.sleep(0.08)
            if not found:status='no_announcements_parsed';message='No recruitment links extracted from archive index'
        except Exception as e:
            status='error';message=str(e)[:180]
        health.append({'source':source['name'],'status':status,'found':found,'checked':checked,'message':message})
    # Lab monitoring: only explicit recruiting language can create a review lead.
    for source in config['lab_sources']:
        if source['type']!='lab-recruitment':
            health.append({'source':source['name'],'status':'reference_only','found':0,'checked':0,'message':'Directory/archive; not used to manufacture vacancies'})
            continue
        try:
            rec,why=check_candidate({'url':source['url'],'title':source['name']},source,'lab')
            if rec:
                old=previous.get(rec['id'],{})
                rec['first_seen']=old.get('first_seen',rec['first_seen'])
                review[rec['id']]=rec
                health.append({'source':source['name'],'status':'review_lead','found':1,'checked':1})
            else:
                reject(why)
                if why=='lab explicitly reports no open positions':verified_closed.add(stable_id(source['url']))
                health.append({'source':source['name'],'status':'no_confirmed_opening','found':0,'checked':1,'message':why})
        except Exception as e:
            health.append({'source':source['name'],'status':'error','found':0,'checked':0,'message':str(e)[:160]})
    # Preserve older records where the currently running collector couldn't recheck them. Exclude expired.
    for id,old in previous.items():
        if id in accepted or id in review or id in verified_closed:continue
        if old.get('deadline') and old['deadline']<TODAY.isoformat():continue
        # Unconfirmed mailing-list notices expire from public review after 180 days.
        if 'mhonarc/' in old.get('url','') and old.get('posted_at'):
            try:
                if (TODAY-dt.date.fromisoformat(old['posted_at'])).days>180:continue
            except ValueError:pass
        old=dict(old);old['verification']='recheck_required'
        review[id]=old
    # Show regional availability and exact source outcomes without exaggerating coverage.
    regional={}
    for rec in list(accepted.values())+list(review.values()):
        key=rec.get('region') or 'Unspecified'
        regional[key]=regional.get(key,0)+1
    output={'schema_version':2,'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'opportunities':list(accepted.values()),'review_queue':list(review.values()),'source_health':health,'rejected_reasons':rejected,'page_errors':errors[:60], 'sources_checked':sum(h.get('checked',0) for h in health),'regional_counts':regional,'search_profiles':SEARCH_PROFILES, 'search_terms':{'include_phrases':ACTIVE_PHRASES,'exclude_phrases':[]}}
    feedfile.parent.mkdir(parents=True,exist_ok=True)
    feedfile.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(f"Verified {len(accepted)}, review {len(review)}, failed sources {sum(x['status']=='error' for x in health)}")
if __name__=='__main__':run()
