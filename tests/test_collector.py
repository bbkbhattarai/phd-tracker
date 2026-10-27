import sys, unittest, datetime as dt
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect
FUTURE=(dt.datetime.now(dt.timezone.utc).date()+dt.timedelta(days=35)).strftime('%d %B %Y')
PAST=(dt.datetime.now(dt.timezone.utc).date()-dt.timedelta(days=10)).strftime('%d %B %Y')
def page(title,body):return '<html><head><title>'+title+'</title></head><body><h1>'+title+'</h1><p>'+body+'</p></body></html>'
class CollectorTests(unittest.TestCase):
 def test_open_funded_vacancy(self):
  text=page('PhD student in auditory neuroscience','Apply now. Application deadline: '+FUTURE+'. This fully funded studentship includes tuition fees and stipend.')
  item,reason=collect.qualify('https://uni.example.edu/jobs/34',text,'Test')
  self.assertIsNone(reason);self.assertEqual(item['deadline'],(dt.datetime.now(dt.timezone.utc).date()+dt.timedelta(days=35)).isoformat());self.assertEqual(item['funding_status'],'explicit')
 def test_old_job_rejected(self):
  item,reason=collect.qualify('https://uni.example.edu/jobs/34',page('PhD hearing researcher','Apply now. Application deadline: '+PAST),'Test')
  self.assertIsNone(item);self.assertEqual(reason,'expired_deadline')
 def test_news_rejected(self):
  item,reason=collect.qualify('https://uni.example.edu/news/34',page('News: Our lab hosts PhD auditory neuroscience graduates','Learn about our work and conference publications, publications about hearing.'),'Test')
  self.assertIsNone(item)
 def test_mixed_deadlines_rejected(self):
  item,reason=collect.qualify('https://uni.example.edu/job/34',page('PhD audiology researcher','Apply now. Application deadline: '+FUTURE+'. Final date for applications: '+PAST+'.'),'Test')
  self.assertIsNone(item);self.assertEqual(reason,'conflicting_deadlines_review')
 def test_missing_deadline_rejected(self):
  item,reason=collect.qualify('https://uni.example.edu/job/34',page('PhD auditory studentship','Apply now. We offer research training in hearing science.'),'Test')
  self.assertIsNone(item);self.assertEqual(reason,'deadline_or_rolling_intake_unverified')
 def test_postdoc_rejected(self):
  item,reason=collect.qualify('https://uni.example.edu/job/34',page('Postdoctoral researcher in PhD auditory neuroscience','Apply now. Application deadline: '+FUTURE),'Test')
  self.assertIsNone(item)
 def test_review_queue_no_deadline(self):
  raw=page('PhD auditory studentship','Apply now. We offer research training in hearing science.')
  item,reason=collect.qualify('https://uni.example.edu/job/34',raw,'Test')
  review=collect.review_candidate('https://uni.example.edu/job/34',raw,'Test',reason)
  self.assertIsNotNone(review);self.assertEqual(review['deadline_status'],'needs_manual_review')
 def test_review_queue_excludes_news(self):
  raw=page('PhD auditory studentship','Apply now. Hearing research.')
  review=collect.review_candidate('https://uni.example.edu/news/34',raw,'Test','deadline_or_rolling_intake_unverified')
  self.assertIsNone(review)
if __name__=='__main__':unittest.main()
