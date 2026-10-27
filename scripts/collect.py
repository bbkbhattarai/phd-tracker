#!/usr/bin/env python3
"""Conservative RSS lead discovery. Google News is not a complete source of PhD vacancies."""
import datetime as dt, hashlib, json, pathlib, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1]; output=ROOT/'data/opportunities.json'
config=json.loads((ROOT/'scripts/sources.json').read_text())
existing=json.loads(output.read_text()) if output.exists() else {'opportunities':[]}
items={x['id']:x for x in existing.get('opportunities',[]) if x.get('id') and x.get('url')}
queries=list(config.get('queries',[]))
# Stagger site-scoped queries across days to reduce throttling and avoid implying
# every university website was searched on every run.
catalog=json.loads((ROOT/config.get('catalog_file','data/source_catalog.json')).read_text()).get('sources',[])
programmes=[s for s in catalog if s.get('kind')=='institution']
slot=dt.datetime.now(dt.timezone.utc).date().toordinal()
batch=min(max(int(config.get('daily_catalog_batch',14)),1),25)
selected=[programmes[(slot*batch+i)%len(programmes)] for i in range(min(batch,len(programmes)))] if programmes else []
for s in selected:
    hostname=urllib.parse.urlsplit(s['url']).hostname
    if hostname: queries.append('site:'+hostname+' PhD (auditory OR hearing OR audiology OR cochlear OR psychoacoustic)')

for site in config.get('custom_sites',[]):
    if re.fullmatch(r'[a-zA-Z0-9.-]+',site): queries.append('site:'+site+' PhD (auditory OR hearing OR audiology OR cochlear)')
# Use explicit geographic signals only; a globally indexed result is not necessarily
# based in the country from which it was searched. Unknown remains Unspecified.
REGIONS = [
 ('Hong Kong', r'\bhong kong\b|\bhkust\b|\bhku\b|\bcuhk\b|\bpolyu\b'),
 ('New Zealand', r'\bnew zealand\b|\bauckland\b|\botago\b|\bcanterbury\b|\bwaikato\b'),
 ('Australia', r'\baustralia\b|\baustralian\b|\bmelbourne\b|\bsydney\b|\bbrisbane\b|\bmacquarie\b|\bmonash\b|\badelaide\b|\bperth\b|\bunsw\b'),
 ('Canada', r'\bcanada\b|\bcanadian\b|\btoronto\b|\bmontreal\b|\bmcgill\b|\bvancouver\b|\bwestern university\b|\bubc\b'),
 ('USA', r'\busa\b|\bu\.s\.a\.\b|\bunited states\b|\bamerican university\b|\bnorthwestern university\b|\bvanderbilt\b|\bjohns hopkins\b|\bpittsburgh\b|\biowa\b'),
 ('UK', r'\buk\b|\bu\.k\.\b|\bunited kingdom\b|\bbritain\b|\bbritish\b|\bengland\b|\bscotland\b|\bwales\b|\blondon\b|\bnottingham\b|\bmanchester\b|\bsheffield\b|\bsouthampton\b|\bucl\b'),
 ('Europe', r'\beurope\b|\beuropean\b|\bgermany\b|\bgerman\b|\bnetherlands\b|\bdutch\b|\bbelgium\b|\bdenmark\b|\bdanish\b|\bsweden\b|\bnorway\b|\bfinland\b|\bfrance\b|\bswitzerland\b|\baustria\b|\bitaly\b|\bspain\b|\boldenburg\b|\bgottingen\b|\bgöttingen\b|\bmaastricht\b|\bradboud\b|\bleuven\b|\bdtu\b'),
 ('Asia', r'\basia\b|\bsingapore\b|\bjapan\b|\bkorea\b|\bindia\b|\bchina\b|\btaiwan\b|\bmalaysia\b|\bnepal\b|\bthailand\b|\btokyo\b|\bseoul\b|\bnus\b|\bntu\b'),
]
DOMAIN_REGIONS = [('.ac.uk','UK'),('.edu.au','Australia'),('.ac.nz','New Zealand'),('.edu.hk','Hong Kong'),('.ac.hk','Hong Kong'),('.ca','Canada'),('.nl','Europe'),('.be','Europe'),('.de','Europe'),('.dk','Europe'),('.se','Europe'),('.no','Europe'),('.fi','Europe'),('.fr','Europe'),('.ch','Europe'),('.at','Europe'),('.sg','Asia'),('.ac.jp','Asia')]
def detect_region(title, source_url=''):
    title=title.lower()
    for region,pattern in REGIONS:
        if re.search(pattern,title,re.I): return region
    host=(urllib.parse.urlsplit(source_url).hostname or '').lower()
    for suffix,region in DOMAIN_REGIONS:
        if host.endswith(suffix): return region
    return 'Unspecified'

for old in items.values():
    if not old.get('region') or old.get('region') == 'Unspecified':
        old['region']=detect_region(old.get('title',''))

headers={'User-Agent':'Mozilla/5.0 (compatible; PhDRadar/1.0; research opportunity discovery)'}
found=0; checked=0; errors=[]
for query in queries:
    url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':query,'hl':'en-GB','gl':'GB','ceid':'GB:en'})
    try:
        req=urllib.request.Request(url,headers=headers)
        with urllib.request.urlopen(req,timeout=18) as response: xml=response.read(1_500_000)
        root=ET.fromstring(xml);checked+=1
        for node in root.findall('.//item'):
            title=(node.findtext('title') or '').strip();link=(node.findtext('link') or '').strip()
            if not title or not link:continue
            low=title.lower()
            if not re.search(r'\b(phd|doctoral|doctorate|studentship|doctoral researcher|doctoral position)\b',low):continue
            if not re.search(r'auditory|hearing|audiolog|cochlear|psychoacoustic|speech perception|ear research|neuroscien',low):continue
            if re.search(r'\b(masters|msc|bachelor|undergraduate)\b',low):continue
            uid=hashlib.sha256(link.encode()).hexdigest()[:20]
            if uid in items:continue
            source=node.find('source');source_name=source.text if source is not None else 'Google News RSS'; source_url=source.attrib.get('url','') if source is not None else ''
            items[uid]={'id':uid,'title':title,'url':link,'organisation':'Verify institution at original link','source':source_name,'region':detect_region(title,source_url),'field':'Hearing & auditory research','discovered':dt.datetime.now(dt.timezone.utc).date().isoformat(),'deadline':None,'summary':'Unverified discovery lead. Check funding, PhD status, deadline and availability on the institution website.'}
            found+=1
    except Exception as exc:errors.append({'query':query,'error':str(exc)[:180]})
cutoff=(dt.datetime.now(dt.timezone.utc).date()-dt.timedelta(days=120)).isoformat()
items={k:v for k,v in items.items() if v.get('discovered','')>=cutoff}
result={'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),'catalog_sources':len(catalog),'catalog_sources_queried_today':len(selected),'source_checks':checked,'new_leads':found,'coverage':'Worldwide (source-matched, not exhaustive)','errors':errors,'opportunities':sorted(items.values(),key=lambda x:x['discovered'],reverse=True)[:500],'note':'Discovery leads only. Deadlines and openings are not verified; do not treat feed absence as exhaustive search.'}
output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(f'checked={checked} new={found} errors={len(errors)} retained={len(result["opportunities"])}')
if queries and checked==0: raise SystemExit('All searches failed. Existing feed was preserved but workflow will fail.')
