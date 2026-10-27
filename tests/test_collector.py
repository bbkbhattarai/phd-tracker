import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('collector',Path(__file__).resolve().parents[1]/'scripts/collect.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

def test_findaphd_links():
    html='<html><a href="/phds/project/hearing-impairment/?p199593=">Auditory Neuroscience and Hearing Loss Project</a><a href="/guides">PhD advice</a></html>'
    results=c.extract_findaphd_links(html,'https://www.findaphd.com/phds/?Keywords=hearing')
    assert len(results)==1 and '/phds/project/' in results[0]['url']

def test_open_advert():
    text='University of Leicester November 23, 2026 Competition Funded PhD Project. Applications are invited to apply for this PhD studentship researching hearing loss and audiology.'
    rec,why=c.classify('Hearing loss doctoral PhD project',text,is_findaphd=True)
    assert not why and rec['deadline']=='2026-11-23' and rec['category']=='advertised_phd'

def test_lab_needs_recruiting():
    rec,why=c.classify('Auditory neuroscience lab','Our neuroscience group studies hearing. We have PhD graduate students.',origin='lab')
    assert rec is None
    rec,why=c.classify('Auditory neuroscience lab','We are recruiting PhD students in auditory neuroscience to join our lab.',origin='lab')
    assert rec and rec['category']=='lab_recruiting'

def test_explicit_closed_lab():
    t='Institute for Auditory Neuroscience Jobs PhD Student Position. There are currently no open positions at the Institute for Auditory Neuroscience.'
    rec,why=c.classify('Göttingen Auditory Neuroscience',t,origin='lab')
    assert rec is None and why=='lab explicitly reports no open positions'

def test_exclusion():
    rec,why=c.classify('Postdoctoral Fellow in Auditory Neuroscience','Applications open for PhD work on hearing.')
    assert rec is None

def test_expired():
    rec,why=c.classify('PhD project in audiology','Deadline: 12 October 2025. Apply to our studentship in hearing science.')
    assert rec is None and why=='deadline passed'

if __name__=='__main__':
    for name,obj in sorted(globals().items()):
        if name.startswith('test_'):
            obj();print('PASS',name)
