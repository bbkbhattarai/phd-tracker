"""Offline fixtures for the new discovery adapters. No invented live results."""
import importlib.util
from pathlib import Path
from unittest.mock import patch
from tempfile import TemporaryDirectory
import json
spec=importlib.util.spec_from_file_location('collector',Path(__file__).resolve().parents[1]/'scripts/collect.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

ARCHIVE_INDEX='''<html><a href="msg00321.html">[AUDITORY] PhD Research Assistant Opportunity at UT Dallas</a><a href="msg00338.html">[AUDITORY] PhD openings in Chicago at the Listening Technology Lab</a><a href="msg00001.html">Conference for PhD attendees</a><a href="msg00002.html">Postdoctoral job in cochlear implants</a></html>'''
POST='''<html><h1>[AUDITORY] PhD openings in Chicago at the Listening Technology Lab</h1><hr><pre>Date: Tue, 13 Oct 2026 15:10:32 +0000</pre><hr><pre>Dr. Ryan Corey at the University of Illinois Chicago is recruiting one or more PhD students to start in Fall 2027. The Listening Technology Lab studies audio and acoustic signal processing for systems that enhance and augment human hearing. Research assistants receive a competitive stipend, tuition waiver, and benefits. Prospective students are encouraged to apply by December 15 to receive an application fee waiver.</pre><hr></html>'''
POST_UTD='''<html><h1>PhD Research Assistant Opportunity at UT Dallas</h1><hr><pre>Date: Mon, 5 Oct 2026 10:04:35 -0500</pre><hr><pre>Dr. Kelly Jahn is recruiting a PhD student in auditory perception, hearing disorders, and EEG. A monthly stipend, tuition support, and health insurance are provided. The upcoming application deadline is November 15.</pre><hr></html>'''
UCL='''<html><main><h1>Improving school-age health outcomes for deaf children with cochlear implants (SOCI)</h1><p>Fully funded PhD studentship. Apply for this doctoral project working on hearing outcomes.</p><p>Application deadline: Apply by 5 pm (GMT), Friday 11 December 2026</p></main></html>'''

def test_archive_index_recruitment_only():
    x=c.archive_links(ARCHIVE_INDEX,'https://www.auditory.org/mhonarc/2026/threads.html')
    assert len(x)==2, x
    assert x[0]['title'].startswith('PhD')

def test_archive_extract_fall_intake_and_no_guessed_year():
    title,body,date=c.archive_post(POST)
    assert date.isoformat()=='2026-10-13'
    assert 'hearing' in body
    rec,why=c.classify(title,body)
    assert rec and rec['category']=='advertised_phd',why
    details=c.extraction_details(body)
    assert details['intake']=='Fall 2027',details
    assert 'December 15' in details['deadline_note'],details
    assert rec['deadline'] is None, 'No-year deadline must not be incorrectly guessed'

def test_archive_utd():
    title,body,date=c.archive_post(POST_UTD)
    assert date.isoformat()=='2026-10-05'
    rec,why=c.classify(title,body)
    assert rec and rec['funding'].startswith('Funding'),(rec,why)
    assert 'November 15' in c.extraction_details(body)['deadline_note']

def test_direct_university_closing_date():
    record,reason=c.check_candidate({'url':'https://www.ucl.ac.uk/example','title':'UCL cochlear implant PhD'}, {'name':'UCL','region':'UK'}) if False else (None,None)
    soup=c.BeautifulSoup(UCL,'html.parser')
    record,reason=c.classify('UCL PhD hearing and cochlear implants',soup.get_text(' ',strip=True),fallback='UK')
    assert not reason and record['deadline']=='2026-12-11',(record,reason)

def test_closed_lab_not_reinstated():
    rec,reason=c.classify('Göttingen auditory PhD lab','There are currently no open positions at the Institute for Auditory Neuroscience. PhD studentship roles include hearing research.',origin='lab')
    assert not rec and 'no open' in reason

if __name__=='__main__':
    for name,fn in sorted(globals().items()):
        if name.startswith('test_') and callable(fn):
            fn();print('PASS',name)
