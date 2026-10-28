"""Offline regression tests for the search-phrase editor's server-side configuration."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('collector', ROOT / 'scripts' / 'collect.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

class SearchCriteriaTests(unittest.TestCase):
    def test_default_topics_from_file(self):
        self.assertIn('cochlear implant', c.SEARCH_TERMS['include_phrases'])
        self.assertTrue(c.HEARING.search('auditory neuroscience funded PhD'))

    def test_configured_phrases_are_literal(self):
        pat = c.phrase_pattern(['auditory brainstem response', 'C++'])
        self.assertTrue(pat.search('PhD in AUDITORY BRAINSTEM RESPONSE'))
        self.assertTrue(pat.search('C++ design'))
        self.assertFalse(pat.search('auditory in brainstem and response'))

    def test_reject_invalid_config(self):
        with self.assertRaises(ValueError):
            c.validate_terms({'include_phrases': [], 'exclude_phrases': []})
        with self.assertRaises(ValueError):
            c.validate_terms({'include_phrases': [99], 'exclude_phrases': []})

    def test_deduplicate_terms(self):
        result = c.validate_terms({'include_phrases': ['HEARING', ' hearing ', 'auditory  neuroscience'], 'exclude_phrases': []})
        self.assertEqual(result['include_phrases'], ['HEARING', 'auditory neuroscience'])

    def test_valid_future_phd_classification(self):
        record,why = c.classify('PhD studentship in cochlear implant research',
            'Applications are open. Application deadline: 31 January 2027. Fully funded PhD studentship.',
            'listing', 'UK')
        self.assertIsNone(why)
        self.assertEqual(record['verification'], 'deadline_verified')
        self.assertEqual(record['deadline'], '2027-01-31')

    def test_expired_phd_rejected(self):
        record,why = c.classify('PhD studentship in cochlear implant research',
            'Applications close: 31 January 2025.', 'listing', 'UK')
        self.assertIsNone(record)
        self.assertEqual(why, 'deadline passed')

    def test_postgrad_index_extracts_subject_link(self):
        html = '''<html><main>
          <section class="tile"><h3><a href="/opportunity/funded-phd-in-auditory-neuroscience/12345">Funded PhD in auditory neuroscience</a></h3><p>Applications now open</p></section>
          <section class="tile"><h3><a href="/opportunity/masters-in-marketing/2222">Masters in Marketing</a></h3></section>
          <nav><a href="/funding-opportunities/">Funding overview</a></nav>
        </main></html>'''
        items=c.institution_links(html,'https://www.postgraduatestudentships.co.uk/funding-opportunities/','postgraduate_funding')
        self.assertEqual(len(items),1)
        self.assertIn('12345',items[0]['url'])

    def test_unrelated_phd_not_imported(self):
        record,why=c.classify('PhD in plant bioengineering',
          'Applications open. Deadline: 2 March 2027. Funded PhD studentship in plants.',
          'listing','UK')
        self.assertIsNone(record)
        self.assertEqual(why,'no configured research phrase matched')

if __name__ == '__main__':unittest.main()

class ProfileTests(unittest.TestCase):
    def test_profile_tiers(self):
        profile={'id':'demo','name':'Hearing and neuroscience','enabled':True,'match_level':'focused',
          'core_phrases':['cochlear implant'], 'related_phrases':['sensory neuroscience'],
          'exploratory_phrases':['bioengineering'], 'exclude_phrases':[],
          'categories':['advertised_phd'], 'regions':[]}
        original=c.SEARCH_PROFILES
        try:
            c.SEARCH_PROFILES={'schema_version':1,'profiles':[profile]}
            self.assertEqual(len(c.match_profiles('funded cochlear implant PhD','advertised_phd','UK')),1)
            self.assertEqual(c.match_profiles('PhD sensory neuroscience','advertised_phd','UK'),[])
            profile['match_level']='balanced'
            self.assertEqual(c.match_profiles('PhD sensory neuroscience','advertised_phd','UK')[0]['score'],70)
            profile['match_level']='exploratory'
            self.assertEqual(c.match_profiles('bioengineering PhD','advertised_phd','UK')[0]['score'],40)
            self.assertEqual(c.match_profiles('cochlear implant PhD','lab_recruiting','UK'),[])
            profile['regions']=['USA']
            self.assertEqual(c.match_profiles('cochlear implant PhD','advertised_phd','UK'),[])
        finally:c.SEARCH_PROFILES=original

    def test_profile_specific_exclusion(self):
        profile={'id':'demo','name':'Example','enabled':True,'match_level':'focused',
          'core_phrases':['hearing'], 'related_phrases':[],'exploratory_phrases':[],
          'exclude_phrases':['hearing protection equipment'],
          'categories':['advertised_phd'], 'regions':[]}
        original=c.SEARCH_PROFILES
        try:
            c.SEARCH_PROFILES={'schema_version':1,'profiles':[profile]}
            self.assertEqual(c.match_profiles('hearing protection equipment PhD','advertised_phd','UK'),[])
            self.assertEqual(len(c.match_profiles('hearing perception PhD','advertised_phd','UK')),1)
        finally:c.SEARCH_PROFILES=original

    def test_reject_all_disabled_profiles(self):
        with self.assertRaises(ValueError):c.validate_profiles({'profiles':[{'id':'test','name':'Test','enabled':False}]})
