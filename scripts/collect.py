#!/usr/bin/env python3
"""Conservative RSS lead discovery. Google News is not a complete source of PhD vacancies."""
import datetime as dt, hashlib, json, pathlib, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1]; output=ROOT/'data/opportunities.json'
config=json.loads((ROOT/'scripts/sources.json').read_text())
existing=json.loads(output.read_text()) if output.exists() else {'opportunities':[]}
items={x['id']:x for x in existing.get('opportunities',[]) if x.get('id') and x.get('url')}
queries=list(config.get('queries',[]))
for site in config.get('custom_sites',[]):
    if re.fullmatch(r'[a-zA-Z0-9.-]+',site): queries.append('site:'+site+' PhD (auditory OR hearing OR audiology OR cochlear)')
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
            source=node.find('source');source_name=source.text if source is not None else 'Google News RSS'
            items[uid]={'id':uid,'title':title,'url':link,'organisation':'Verify institution at original link','source':source_name,'field':'Hearing & auditory research','discovered':dt.datetime.now(dt.timezone.utc).date().isoformat(),'deadline':None,'summary':'Unverified discovery lead. Check funding, PhD status, deadline and availability on the institution website.'}
            found+=1
    except Exception as exc:errors.append({'query':query,'error':str(exc)[:180]})
cutoff=(dt.datetime.now(dt.timezone.utc).date()-dt.timedelta(days=120)).isoformat()
items={k:v for k,v in items.items() if v.get('discovered','')>=cutoff}
result={'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),'source_checks':checked,'new_leads':found,'errors':errors,'opportunities':sorted(items.values(),key=lambda x:x['discovered'],reverse=True)[:500],'note':'Discovery leads only. Deadlines and openings are not verified; do not treat feed absence as exhaustive search.'}
output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(f'checked={checked} new={found} errors={len(errors)} retained={len(result["opportunities"])}')
if queries and checked==0: raise SystemExit('All searches failed. Existing feed was preserved but workflow will fail.')
