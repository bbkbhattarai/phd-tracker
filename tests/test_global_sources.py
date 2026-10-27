"""Offline tests for legitimate worldwide vacancy and recruiting-lab pages."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import datetime as dt
spec=importlib.util.spec_from_file_location('global_collector',Path(__file__).resolve().parents[1]/'scripts/collect.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
c.TODAY=dt.date(2026,10,27)

def test_europe_bcbl_day_first():
    text='PhD position in auditory processing precision and EEG. We are looking for a PhD student. Application deadline: 08/11/2026. Funding sources: Spanish Ministry of Science.'
    rec,error=c.classify('BCBL PhD position auditory processing',text,fallback='Europe')
    assert error is None,(rec,error)
    assert rec['deadline']=='2026-11-08'
    assert rec['verification']=='deadline_verified'

def test_macquarie_australian_close_date():
    text='This cochlear implantation hearing research PhD scholarship is accepting applications. Applications close on 1 March 2027. Domestic, International. $40,900 p.a.'
    rec,error=c.classify('National cochlear implantation guidelines PhD scholarship',text,fallback='Australia')
    assert not error,(rec,error)
    assert rec['deadline']=='2027-03-01'
    assert rec['region']=='Australia'

def test_ucl_and_oxford_dates():
    ucl='Fully funded PhD studentship in hearing and cochlear implants. Application deadline: Apply by 5 pm (GMT), Friday 11 December 2026.'
    ox='The University of Oxford auditory stimulation DPhil research studentship is open for applications. The closing date for applications is 12.00 midday UK time on Tuesday 1st December 2026.'
    a,err=c.classify('UCL cochlear implant PhD',ucl,fallback='UK')
    b,err2=c.classify('Oxford DPhil auditory stimulation',ox,fallback='UK')
    assert (a or {}) .get('deadline')=='2026-12-11',(a,err)
    assert (b or {}).get('deadline')=='2026-12-01',(b,err2)

def test_hongkong_cuhk_review_without_invented_date():
    text='We are accepting PhD students for the upcoming academic year. The laboratory studies speech perception and auditory processing, language and brain research. Please submit your CV with your inquiry.'
    rec,error=c.classify('CUHK Language Learning and Brain Lab',text,origin='lab',fallback='Hong Kong')
    assert rec and not error,(rec,error)
    assert rec['deadline'] is None and rec['region']=='Hong Kong'

def test_new_zealand_lab_recruitment():
    text='Positions are available for students to pursue Doctor of Philosophy (PhD). The Communication Acoustics Laboratory studies the science of hearing, psychoacoustics and speech processing. Prospective candidates should send their CV.'
    rec,error=c.classify('Auckland Communication Acoustics Lab',text,origin='lab',fallback='New Zealand')
    assert rec and not error,(rec,error)
    assert rec['verification']=='review_required'

def test_canadian_cochlear_neuroscience_recruitment():
    text='McGill Cochlear Implant Research Program. Auditory cognitive neuroscience, hearing loss and brain plasticity. Currently Recruiting Ph.D. Students. Research graduate students should contact Prof. Lehmann.'
    rec,error=c.classify('McGill Cochlear Implant Lab',text,origin='lab',fallback='Canada')
    assert rec and not error,(rec,error)
    assert rec['region']=='Canada'
    assert rec['funding']=='Student funding not confirmed'

def test_closed_and_generic_pages_rejected():
    closed='There are currently no open positions at the auditory neuroscience laboratory. Past hearing PhD students and funded projects are listed.'
    a,why=c.classify('Göttingen auditory neuroscience',closed,origin='lab',fallback='Europe')
    assert not a and why=='lab explicitly reports no open positions'
    generic='Our doctoral programme in hearing sciences teaches audiology and has PhD students. We publish research and host talks.'
    b,why2=c.classify('Audiology doctoral degree information',generic,origin='lab',fallback='Canada')
    assert not b

def test_institution_index_only_specific_project_links():
    html='''<html><a href="/jobs">All jobs</a><article><h3>PhD position - AUDITORY PROCESSING (EEG)</h3><a href="/eu/phd-position-auditory-processing-l2">More information and registration</a></article><a href="/eu/postdoctoral-neuroscience">Postdoc</a></html>'''
    links=c.institution_links(html,'https://www.bcbl.eu/en/join-us/job-offers','bcbl_jobs')
    assert len(links)==1,links
    assert 'auditory-processing' in links[0]['url']

def test_pipeline_keeps_old_and_adds_regions():
    with TemporaryDirectory() as temp:
        root=Path(temp);(root/'scripts').mkdir();(root/'data').mkdir()
        base='https://example.org/'
        config={'listing_sources':[], 'institution_indexes':[], 'announcement_sources':[], 'reference_sources':[],
          'direct_vacancies':[{'name':'AU Macquarie PhD','title':'PhD hearing cochlear','url':base+'aus','region':'Australia'}],
          'lab_sources':[{'name':'CUHK recruiting PhDs','type':'lab-recruitment','url':base+'hk','region':'Hong Kong'}]}
        (root/'scripts/sources.json').write_text(json.dumps(config))
        (root/'data/opportunities.json').write_text(json.dumps({'opportunities':[],'review_queue':[]}))
        pages={base+'aus':'<html><main>PhD cochlear hearing studentship. Apply now. Applications close on 1 March 2027. Funded scholarship.</main></html>',
               base+'hk':'<html><main>We are accepting PhD students for auditory and speech perception in the upcoming academic year. Graduate students should send their CV.</main></html>'}
        def fetch(url):return pages[url],url
        with patch.object(c,'ROOT',root), patch.object(c,'fetch',side_effect=fetch):
            c.run()
        data=json.loads((root/'data/opportunities.json').read_text())
        assert len(data['opportunities'])==1,data
        assert len(data['review_queue'])==1,data
        assert data['regional_counts']=={'Australia':1,'Hong Kong':1}
