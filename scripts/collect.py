#!/usr/bin/env python3
"""PhD Research Radar v1.3: vacancy-first discovery with conservative validation.
No arbitrary news articles. No claims of openness without a future deadline/rolling intake.
Designed for GitHub Actions with Python standard library only.
"""
import datetime as dt
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
CATALOG=json.loads((ROOT/'data/source_catalog.json').read_text())
TODAY=dt.datetime.now(dt.timezone.utc).date()
CFG=json.loads((ROOT/'scripts/sources.json').read_text())
OUT=ROOT/'data/opportunities.json'
OLD=json.loads(OUT.read_text()) if OUT.exists() else {}
UA={'User-Agent':'Mozilla/5.0 (compatible; PhDResearchRadar/1.4; public vacancy validation)'}
HEARING=re.compile(r'\b(auditory|audiolog\w*|hearing|cochlear|psychoacoustic\w*|speech.in.noise|speech perception|auditory processing|sound localisation|sound localization|vestibular|otoacoustic|electrophysiolog\w*|auditory neuroscience|hearing aid\w*)\b',re.I)
PHD=re.compile(r'\b(ph\.?d\.?|doctoral (?:candidate|student|researcher|position|studentship|programme|program)|doctorate|dphil|doctoral degree|funded studentship)\b',re.I)
TITLE_PHD=re.compile(r'\b(ph\.?d\.?|doctoral (?:candidate|researcher|student|position)|studentship|dphil)\b',re.I)
EXCLUDE=re.compile(r'\b(postdoc\w*|post.doctoral|assistant professor|associate professor|faculty position|news|blog|research paper|journal|conference|workshop|webinar|alumni|masters programme|msc course|bachelor|undergraduate|audiology doctorate \(aud\)|doctor of audiology)\b',re.I)
OPEN=re.compile(r'\b(apply now|apply for this|applications? (?:are |is )?(?:invited|open|welcome|accepted)|how to apply|submit (?:your |an )?application|application (?:form|process|portal)|vacanc(?:y|ies)|job offer|job opportunities|funded phd|funded doctoral)\b',re.I)
CLOSED=re.compile(r'\b(status\s*:\s*expired|applications? (?:are |is )?closed|vacancy (?:has )?closed|position filled|applications? no longer accepted|this opportunity has closed|advert has expired)\b',re.I)
ROLLING=re.compile(r'\b(rolling admissions|applications? accepted (?:year.round|throughout the year)|year.round applications|open until filled)\b',re.I)
MONTHS='January February March April May June July August September October November December'.split()
MONTH_RE='|'.join(MONTHS+[x[:3] for x in MONTHS]+['Sept'])
DEADLINE_CONTEXT=re.compile(r'\b(?:application deadline|closing date|applications close|deadline for (?:applications|applying)|final date for applications|closes|apply by)\b\s*[:\-]?\s*(.{0,100})',re.I)
DATE_ISO=re.compile(r'\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b')
DATE_DMY=re.compile(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+('+MONTH_RE+r')\.?[,]?\s+(20\d{2})\b',re.I)
DATE_NUM=re.compile(r'\b(\d{1,2})/(\d{1,2})/(20\d{2})\b')
REGION_DOMAINS=[('.ac.uk','UK'),('.edu.au','Australia'),('.ac.nz','New Zealand'),('.edu.hk','Hong Kong'),('.ac.hk','Hong Kong'),('.ca','Canada'),('.nl','Europe'),('.be','Europe'),('.de','Europe'),('.dk','Europe'),('.se','Europe'),('.no','Europe'),('.fr','Europe'),('.ch','Europe'),('.sg','Asia')]
COUNTRIES=[('Hong Kong',r'\bhong kong\b'),('New Zealand',r'\bnew zealand\b'),('Australia',r'\baustralia\b'),('Canada',r'\bcanada\b'),('USA',r'\bunited states\b|\busa\b'),('UK',r'\bunited kingdom\b|\bengland\b|\bscotland\b|\bwales\b'),('Europe',r'\bnetherlands\b|\bspain\b|\bfrance\b|\bgermany\b|\bdenmark\b|\bbelgium\b|\bnorway\b|\bsweden\b|\bswitzerland\b|\bitaly\b'),('Asia',r'\bsingapore\b|\bchina\b|\bjapan\b|\bindia\b|\btaiwan\b|\bkorea\b')]

class Page(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True);self.parts=[];self.links=[];self.title=[];self.h1=[];self.suppress=0;self.in_title=False;self.in_h1=False;self.meta={}
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag in ('script','style','noscript','svg'):self.suppress+=1
  if tag=='title':self.in_title=True
  if tag=='h1':self.in_h1=True
  if tag=='a' and a.get('href'):self.links.append((a['href'],''))
  if tag=='meta':self.meta[a.get('property') or a.get('name') or '']=a.get('content','')
  if tag in ('p','div','section','li','h1','h2','h3','br','tr','td'):self.parts.append('\n')
 def handle_endtag(self,tag):
  if tag in ('script','style','noscript','svg'):self.suppress=max(0,self.suppress-1)
  if tag=='title':self.in_title=False
  if tag=='h1':self.in_h1=False
  if tag in ('p','div','li','h1','h2','h3','tr'):self.parts.append('\n')
 def handle_data(self,data):
  if self.suppress:return
  self.parts.append(data)
  if self.in_title:self.title.append(data)
  if self.in_h1:self.h1.append(data)
 def text(self):
  raw=''.join(self.parts)
  return re.sub(r'[ \t]+',' ',re.sub(r'\n{3,}','\n\n',raw))

def fetch(url):
 req=urllib.request.Request(url,headers=UA)
 with urllib.request.urlopen(req,timeout=15) as response:
  typ=response.headers.get('Content-Type','')
  if 'pdf' in typ.lower():raise ValueError('PDF unsupported by lightweight extractor')
  return response.read(1_500_000).decode('utf-8','replace')

def parse_date(text):
 m=DATE_ISO.search(text)
 if m:
  try:return dt.date(*map(int,m.groups())).isoformat()
  except ValueError:return None
 m=DATE_DMY.search(text)
 if m:
  day,mon,year=m.groups()
  try:return dt.date(int(year),next(i for i,n in enumerate(MONTHS,1) if n.lower().startswith(mon[:3].lower())),int(day)).isoformat()
  except (ValueError,StopIteration):return None
 m=DATE_NUM.search(text)
 if m:
  a,b,c=map(int,m.groups())
  try:return dt.date(c,b,a).isoformat() if a>12 else None # avoid ambiguous UK/US slash dates
  except ValueError:return None
 return None

def extract_deadlines(text):
 dates=[]
 markers=list(re.finditer(r'\b(?:application deadline|closing date|applications close|deadline for (?:applications|applying)|final date for applications|closes|apply by)\b',text,re.I))
 for i,m in enumerate(markers):
  ending=markers[i+1].start() if i+1<len(markers) else len(text)
  d=parse_date(text[m.start():min(ending,m.start()+130)])
  if d:dates.append(d)
 return sorted(set(dates))

def funding_info(text):
 s=re.sub(r'\s+',' ',text)
 if re.search(r'\bself.funded\b|self funded phd|unfunded phd',s,re.I):return 'Self-funded / unfunded','explicit'
 if re.search(r'\bfully funded\b|tuition (?:fees|waiver).{0,140}\bstipend\b|\bstipend\b.{0,140}\btuition\b',s,re.I):return 'Fully funded claimed','explicit'
 if re.search(r'\bfunding for\s*:\s*uk students\b|\bhome fee status\b',s,re.I):return 'Funding restricted to home/UK students','explicit'
 if re.search(r'\b(?:funded (?:phd|doctoral|studentship|position)|doctoral salary|salary|stipend|scholarship|funding sources)\b',s,re.I):return 'Funding/salary mentioned; details to verify','partial'
 return 'Not specified','missing'

def region_from(text,url):
 for name,pat in COUNTRIES:
  if re.search(pat,text[:3500],re.I):return name
 host=(urllib.parse.urlparse(url).hostname or '').lower()
 for suf,region in REGION_DOMAINS:
  if host.endswith(suf):return region
 return 'Unspecified'

def qualify(url,html_text,source):
 page=Page();page.feed(html_text)
 title=html.unescape((' '.join(page.h1) or ' '.join(page.title) or '').strip())[:240]
 body=page.text()[:90000]
 head=(title+' '+page.meta.get('description',''))[:700]
 if len(body)<45:return None,'incomplete_page'
 path=urllib.parse.urlsplit(url).path.lower()
 if re.search(r'/(news|blog|articles?|press-releases?|events?)/',path):return None,'news_or_article_url'
 if not (TITLE_PHD.search(title) or (PHD.search(head) and OPEN.search(body[:12000]))):return None,'not_doctoral_vacancy'
 if EXCLUDE.search(title):return None,'excluded_postdoc_article_or_course'
 if not HEARING.search(title+' '+body[:6000]):return None,'not_auditory_research'
 if not OPEN.search(body[:18000]):return None,'no_application_evidence'
 if CLOSED.search(body[:13000]):return None,'explicitly_closed'
 dates=extract_deadlines(body[:20000])
 future=[x for x in dates if x>=TODAY.isoformat()]
 if dates and not future:return None,'expired_deadline'
 if len(dates)>1:return None,'conflicting_deadlines_review' # cannot safely choose between admission and vacancy date
 rolling=bool(ROLLING.search(body[:12000]))
 if not future and not rolling:return None,'deadline_or_rolling_intake_unverified'
 deadline=future[0] if future else None
 funding,confidence=funding_info(body[:18000])
 canonical=page.meta.get('og:url') or url
 if not canonical.startswith('https://') and not canonical.startswith('http://'):canonical=url
 source_host=urllib.parse.urlsplit(canonical).hostname or ''
 if 'news.google.com' in source_host:return None,'news_not_original_vacancy'
 uid=hashlib.sha256(canonical.split('?')[0].rstrip('/').encode()).hexdigest()[:20]
 snippet=re.sub(r'\s+',' ',body)[:450]
 # avoid misleading 'verified' about availability: deadline evidence only
 return {'id':uid,'title':title,'url':canonical,'organisation':source_host,'source':source,'region':region_from(title+' '+body[:3000],canonical),'field':'Audiology / auditory / hearing research','discovered':TODAY.isoformat(),'deadline':deadline,'deadline_status':'stated_on_source' if deadline else 'rolling_as_stated','funding':funding,'funding_status':confidence,'verification':'original_page_checked','last_verified':TODAY.isoformat(),'summary':snippet,'vacancy_type':'doctoral_position'},None

def institution_candidates():
 """Rotating targeted discovery, not direct guaranteed monitoring of all institutions."""
 pool=[s for s in CATALOG.get('sources',[]) if s.get('kind') not in ('portal',) and urllib.parse.urlparse(s.get('url','')).hostname]
 batch=int(CFG.get('institution_queries_per_run',12))
 if not pool:return [],[]
 offset=(TODAY.toordinal()*batch)%len(pool)
 chosen=[pool[(offset+i)%len(pool)] for i in range(min(batch,len(pool)))]
 results=[];health=[]
 for s in chosen:
  host=urllib.parse.urlparse(s['url']).hostname
  q=f'site:{host} ("PhD position" OR "PhD studentship" OR "doctoral researcher") (auditory OR audiology OR hearing OR cochlear OR psychoacoustics) (apply OR deadline)'
  try:
   xml=ET.fromstring(fetch('https://www.bing.com/search?'+urllib.parse.urlencode({'q':q,'format':'rss'})))
   count=0
   for node in xml.findall('.//item'):
    link=(node.findtext('link') or '').strip();title=node.findtext('title') or ''
    if not link.startswith('http') or 'bing.com' in (urllib.parse.urlparse(link).hostname or ''):continue
    if (PHD.search(title) or re.search(r'/(job|vacancy|position|studentship)/',link,re.I)) and (HEARING.search(title) or HEARING.search(q)):
     results.append((link,s['name']));count+=1
   health.append({'source':s['name'],'method':'site-index','status':'ok','candidates':count})
  except Exception as ex:health.append({'source':s['name'],'method':'site-index','status':'error','detail':str(ex)[:160]})
 return results,health

def search_candidates():
 """Search ordinary web index, not news indexing, then VERIFY the original vacancy page."""
 candidates=[];diagnostics=[]
 for query in CFG.get('search_queries',[])[:int(CFG.get('max_search_queries',6))]:
  q=query+' (apply OR vacancy OR deadline OR studentship) -postdoc -news -journal'
  url='https://www.bing.com/search?'+urllib.parse.urlencode({'q':q,'format':'rss'})
  try:
   xml=ET.fromstring(fetch(url));count=0
   for node in xml.findall('.//item'):
    link=(node.findtext('link') or '').strip();title=node.findtext('title') or ''
    host=(urllib.parse.urlsplit(link).hostname or '').lower()
    if host.endswith('bing.com') or not link.startswith('http'):continue
    if (PHD.search(title) and HEARING.search(title)) or (PHD.search(title) and OPEN.search(title)):
     candidates.append((link,'Web vacancy discovery'));count+=1
   diagnostics.append({'source':'Web vacancy discovery: '+query,'status':'ok','candidates':count})
  except Exception as err:diagnostics.append({'source':'Web vacancy discovery: '+query,'status':'error','detail':str(err)[:160]})
 return candidates,diagnostics

def direct_candidates():
 out=[];health=[]
 for source in CFG.get('direct_sources',[]):
  url=source['url'];name=source['name']
  try:
   html_text=fetch(url);page=Page();page.feed(html_text)
   if 'captcha' in page.text()[:1200].lower():raise ValueError('CAPTCHA / anti-bot response')
   raw=[]
   for href,_ in page.links:
    candidate=urllib.parse.urljoin(url,href)
    u=urllib.parse.urlsplit(candidate)
    path=(u.path+' '+u.query).lower()
    if u.scheme not in ('http','https') or u.hostname is None:continue
    if re.search(r'/job/|/jobs/\d+|/phds/[^?]+|/phd[-_/]|/vacanc|/positions?/|studentship|job-offers/',path):raw.append(candidate)
   raw=list(dict.fromkeys(raw))[:24]
   out.extend((link,name) for link in raw if link!=url)
   health.append({'source':name,'status':'ok','candidates':len(raw)})
  except Exception as err:health.append({'source':name,'status':'error','detail':str(err)[:160]})
 return out,health

def collect():
 candidates,health=direct_candidates()
 more,diag=search_candidates();candidates.extend(more);health.extend(diag)
 institutions,inst_health=institution_candidates();candidates.extend(institutions);health.extend(inst_health)
 for link in CFG.get('custom_vacancy_urls',[]):candidates.append((link,'Configured vacancy URL'))
 unique={}
 for url,src in candidates:
  key=url.split('#')[0]
  if key not in unique:unique[key]=src
 limit=max(1,int(CFG.get('max_candidate_pages',55)))
 accepted={};rejected={};errors=[]
 for url,source in list(unique.items())[:limit]:
  try:
   item,reason=qualify(url,fetch(url),source)
   if item:accepted[item['id']]=item
   else:rejected[reason]=rejected.get(reason,0)+1
  except Exception as err:errors.append({'url':url,'error':str(err)[:150]})
 # Revalidate old accepted entries: never carry forward unverified legacy news records.
 # Keep a previously verified entry only when it was actually rechecked in this run;
 # when source fails, do not claim that opportunity is still open.
 previous={x['url']:x for x in OLD.get('opportunities',[]) if x.get('verification')=='original_page_checked' and x.get('url') and (not x.get('deadline') or x['deadline']>=TODAY.isoformat())}
 for url,old in previous.items():
  if any(x['url']==url for x in accepted.values()):continue
  if len(accepted)>=500:break
  try:
   fresh,why=qualify(url,fetch(url),old.get('source','Previous verified listing'))
   if fresh:
    fresh['discovered']=old.get('discovered',TODAY.isoformat());accepted[fresh['id']]=fresh
   else:rejected['previous_'+str(why)]=rejected.get('previous_'+str(why),0)+1
  except Exception as err:errors.append({'url':url,'error':'revalidation: '+str(err)[:130]})
 out={'schema_version':3,'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),'coverage':'Worldwide: verified source pages only, non-exhaustive','opportunities':sorted(accepted.values(),key=lambda x:(x['deadline'] or '9999-12-31',x['title']))[:500],'source_health':health,'rejected_reasons':rejected,'page_errors':errors[:60],'candidate_pages':len(unique),'pages_attempted':min(len(unique),limit),'institution_sources_total':len([s for s in CATALOG.get('sources',[]) if s.get('kind')!='portal']),'institution_sources_checked':len(inst_health),'total_sources_checked':len(health),'note':'Only PhD vacancy pages with an explicit future deadline or rolling applications are displayed. Funding may remain unspecified. Conflicting or missing deadlines are withheld. This feed is not exhaustive.'}
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
 print('Candidates:',len(unique),'verified open:',len(accepted),'rejected:',rejected,'errors:',len(errors))
 if not unique and all(x['status']=='error' for x in health):raise SystemExit('All discovery sources failed; feed retained but search not completed')

if __name__=='__main__':collect()
