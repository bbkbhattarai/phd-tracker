"""End-to-end offline fixture: collection writes verified project + archive review."""
import json
import importlib.util
import datetime as dt
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('collector',Path(__file__).resolve().parents[1]/'scripts/collect.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

INDEX='<html><a href="msg00338.html">PhD openings in Chicago at the Listening Technology Lab</a></html>'
POST='<html><h1>PhD openings in Chicago at the Listening Technology Lab</h1><hr><pre>Date: Tue, 13 Oct 2026 15:10:32 +0000</pre><hr><pre>Dr Ryan Corey at the University of Illinois Chicago is recruiting PhD students for Fall 2027. The lab studies auditory hearing devices, acoustic signal processing and hearing technology. We offer research assistant stipends and tuition waiver. Prospective students are encouraged to apply by December 15.</pre></html>'
UCL='<html><main><h1>UCL cochlear implant hearing outcomes PhD studentship</h1><p>Applications are invited for a PhD studentship in hearing science and cochlear implant outcomes. Application deadline: Apply by 5 pm (GMT), Friday 11 December 2026.</p></main></html>'
LAB='<html><main><h1>Illinois Auditory Neuroscience Lab</h1><p>Our lab is seeking PhD candidates to study tinnitus and auditory hearing science. Please contact Dr Fatima Husain.</p></main></html>'

def test_pipeline():
    with TemporaryDirectory() as td:
        root=Path(td);(root/'scripts').mkdir();(root/'data').mkdir()
        config={'listing_sources':[{'name':'FindAPhD hearing','url':'https://findaphd.com/blocked','adapter':'findaphd','region':'Worldwide'}],
                'direct_vacancies':[{'name':'UCL project','url':'https://www.ucl.ac.uk/student','region':'UK'}],
                'announcement_sources':[{'name':'AUDITORY announcements','url':'https://www.auditory.org/mhonarc/2026/threads.html','region':'Worldwide','max_items':5,'max_age_days':120}],
                'lab_sources':[{'name':'Illinois Auditory Lab','url':'https://illinois.edu/join','type':'lab-recruitment','region':'USA'}]}
        (root/'scripts/sources.json').write_text(json.dumps(config))
        (root/'data/opportunities.json').write_text(json.dumps({'opportunities':[],'review_queue':[]}))
        def fake(url):
            if 'blocked' in url:raise RuntimeError('403 Forbidden')
            page=POST if 'msg00338' in url else INDEX if 'threads.html' in url else UCL if 'ucl.ac.uk' in url else LAB
            return page,url
        with patch.object(c,'ROOT',root),patch.object(c,'TODAY',dt.date(2026,10,27)),patch.object(c,'fetch',fake),patch.object(c.time,'sleep',lambda _:None):
            c.run()
        result=json.loads((root/'data/opportunities.json').read_text())
        assert len(result['opportunities'])==1,result
        assert result['opportunities'][0]['deadline']=='2026-12-11'
        assert len(result['review_queue'])==2,result
        assert any('Chicago' in r['title'] and r['intake']=='Fall 2027' for r in result['review_queue'])
        assert any(x['status']=='error' for x in result['source_health'])
        assert result['generated_at']

if __name__=='__main__':
    test_pipeline();print('PASS test_pipeline')
