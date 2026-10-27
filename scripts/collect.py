#!/usr/bin/env python3
"""Vacancy-first collector. No synthetic opportunities. Missing deadlines stay unverified.
Runs in GitHub Actions; archives source-health and previously discovered records.
"""
import datetime as dt
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
HEARING=re.compile(r'\b(hearing|auditor(?:y|ily)|audiolog(?:y|ical)|cochlear|psychoacoustics?|speech[- ]in[- ]noise|listening|binaural|spatial hearing|tinnitus|vestibular|implantable hearing|evoked potentials|ABR|ASSR|CAEP)\b',re.I)
PHD=re.compile(r'\b(ph\.?d\.?|doctoral|doctorate|studentship|graduate student|research student)\b',re.I)
EXCLUDE=re.compile(r'\b(postdoc(?:toral)?|research fellow|faculty position|assistant professor|masters? degree|MSc|AuD only)\b',re.I)
RECRUIT=re.compile(r'\b(apply|applications? (?:are )?(?:open|invited|welcome)|recruiting|seeking|looking for|studentship|funded position|graduate assistantship|doctoral researcher|join (?:the|our) lab|prospective students?|available position|closing date)\b',re.I)

COUNTRY_PATTERNS=[('Hong Kong',r'\bHong Kong\b'),('New Zealand',r'\bNew Zealand\b'),('Australia',r'\bAustralia\b'),('Canada',r'\bCanada\b'),('USA',r'\b(?:USA|United States|U\.S\.A\.|US university|Texas|Illinois|Indiana|California|Maryland|New York|Massachusetts|Pittsburgh|Vanderbilt|Northwestern)\b'),('UK',r'\b(?:United Kingdom|\bUK\b|England|Scotland|Wales|Northern Ireland|Southampton|Leicester|Edinburgh|London|Nottingham|Manchester|Sheffield|Birmingham|Bristol|Oxford|Cambridge)\b'),('Europe',r'\b(?:Germany|Netherlands|Denmark|Sweden|Norway|Finland|Belgium|France|Spain|Italy|Austria|Switzerland|Portugal|Ireland|Göttingen|Oldenburg|Leuven)\b'),('Asia',r'\b(?:Singapore|Japan|China|India|South Korea|Taiwan|Malaysia|Nepal)\b')]
MONTHS='January February March April May June July August September October November December'.split()
DATE_RX=re.compile(r'\b(?:\d{1,2}\s+(?:'+ '|'.join(MONTHS) + r')\s+20\d{2}|(?:'+ '|'.join(MONTHS) + r')\s+\d{1,2},?\s+20\d{2}|20\d{2}-\d{2}-\d{2})\b', re.I)
DEADLINE_RX=re.compile(r'(?:application (?:deadline|closing date)|closing date|deadline|apply by|applications? (?:close|due))\s*[:\-]?\s*(?:on\s+)?(.{0,55})',re.I)

def parse_date(s):
    s=s.strip().replace(',','')
    for fmt in ('%d %B %Y','%B %d %Y','%Y-%m-%d'):
        try:return dt.datetime.strptime(s,fmt).date()
        except ValueError:pass
    return None

def deadline(text):
    for match in DEADLINE_RX.finditer(text[:18000]):
        d=DATE_RX.search(match.group(1))
        if d:
            parsed=parse_date(d.group(0))
            if parsed:return parsed.isoformat()
    return None

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
    if re.search(r'funded|studentship|scholarship|assistantship|stipend',t):return 'Funding mentioned (details unverified)'
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

def classify(title,content,origin='listing',fallback='Unspecified',is_findaphd=False):
    text=(title+' '+content).strip()
    short=text[:18000]
    if EXCLUDE.search(title):return None,'non-doctoral role'
    if not HEARING.search(short):return None,'not hearing-related'
    if not PHD.search(short):return None,'not doctoral'
    if not RECRUIT.search(short):return None,'no recruitment evidence'
    dl=deadline(short) or (fallback_findaphd_date(short) if is_findaphd else None)
    if dl and dl<TODAY.isoformat():return None,'deadline passed'
    if origin=='lab':
        category='lab_recruiting'
        # Require stronger explicit phrasing for labs, not simply a generic graduate study page.
        if not re.search(r'\b(recruiting|seeking|looking for|positions? available|join (?:the|our) lab|accepting (?:new )?(?:graduate|phd)|graduate students? (?:are )?welcome)\b',short,re.I):
            return None,'no explicit lab recruitment'
    else: category='advertised_phd'
    status='deadline_verified' if dl else 'review_required'
    return {'category':category,'deadline':dl,'funding':funding(short),'region':region(short,fallback),'verification':status,'summary':re.sub(r'\s+',' ',content)[:700]},None

def check_candidate(item,source,kind='listing'):
    url=item['url']
    # Get the actual advert, never substitute an article/headline result.
    html,final=fetch(url)
    soup=BeautifulSoup(html,'html.parser')
    for x in soup(['script','style','nav','footer','header']):x.decompose()
    main=soup.find('main') or soup.find('article') or soup
    body=main.get_text(' ',strip=True)[:20000]
    title=item.get('title') or (soup.title.get_text(' ',strip=True) if soup.title else '')
    if not title:title=(main.find('h1').get_text(' ',strip=True) if main.find('h1') else url)
    detail,why=classify(title,body,'lab' if kind=='lab' else 'listing',source.get('region','Unspecified'),is_findaphd_project(final))
    if not detail:return None,why
    detail.update({'id':stable_id(final),'title':title[:230],'url':final,'source':source['name'],'last_checked':TODAY.isoformat(),'first_seen':TODAY.isoformat(),'evidence':'Page content checked; application status and funding should be confirmed with institution'})
    if kind=='lab':detail['verification']='recruitment_claim_needs_confirmation'
    return detail,None

def run():
    config=json.loads((ROOT/'scripts/sources.json').read_text())
    feedfile=ROOT/'data/opportunities.json'
    prior=json.loads(feedfile.read_text()) if feedfile.exists() else {}
    previous={x['id']:x for x in prior.get('opportunities',[])+prior.get('review_queue',[]) if x.get('id')}
    accepted={}; review={}; health=[]; rejected={}; errors=[]
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
                health.append({'source':source['name'],'status':'no_confirmed_opening','found':0,'checked':1,'message':why})
        except Exception as e:
            health.append({'source':source['name'],'status':'error','found':0,'checked':0,'message':str(e)[:160]})
    # Preserve older records where the currently running collector couldn't recheck them. Exclude expired.
    for id,old in previous.items():
        if id in accepted or id in review:continue
        if old.get('deadline') and old['deadline']<TODAY.isoformat():continue
        old=dict(old);old['verification']='recheck_required'
        review[id]=old
    output={'schema_version':2,'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'opportunities':list(accepted.values()),'review_queue':list(review.values()),'source_health':health,'rejected_reasons':rejected,'page_errors':errors[:60], 'sources_checked':sum(h.get('checked',0) for h in health)}
    feedfile.parent.mkdir(parents=True,exist_ok=True)
    feedfile.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(f"Verified {len(accepted)}, review {len(review)}, failed sources {sum(x['status']=='error' for x in health)}")
if __name__=='__main__':run()
