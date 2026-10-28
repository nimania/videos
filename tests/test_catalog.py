import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('videos_catalog',ROOT/'scripts'/'build_catalog.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class CatalogueTests(unittest.TestCase):
 def setUp(self):
  self.figures={'figures':[
   {'handle':'person-a','name_fa':'نفر اول','youtube_videos':[{'id':'abcdefghijk','url':'https://www.youtube.com/watch?v=abcdefghijk','title':'موضوع اول','published_at':'2026-10-27T15:30:00Z','recap_fa':'خلاصه معتبر'}]},
   {'handle':'person-b','name_fa':'نفر دوم','youtube_videos':[{'id':'abcdefghijk','url':'https://youtu.be/abcdefghijk','title':'موضوع اول','published_at':'2026-10-27T15:30:00Z'}]}]}
 def test_dedup(self):
  rows=mod.normalize(self.figures,[{'video_id':'abcdefghijk','id':'youtube-abcdefghijk'}])
  self.assertEqual(len(rows),1)
  self.assertEqual(len(rows[0]['people']),2)
  self.assertEqual(rows[0]['studio_id'],'youtube-abcdefghijk')
  self.assertTrue(rows[0]['recap_fa'])
 def test_youtube_url_validation(self):
  self.assertEqual(mod.youtube_id('https://youtu.be/abcdefghijk'),'abcdefghijk')
  self.assertEqual(mod.youtube_id('https://evil.example/watch?v=abcdefghijk'),'')
 def test_external_links_are_curated(self):
  links=mod.safe_relations({'abcdefghijk':[{'title':'کتاب','url':'https://nimania.github.io/pishkhan/book/test/'},{'title':'ناامن','url':'javascript:alert(1)'}]})
  self.assertEqual(len(links['abcdefghijk']),1)
 def test_build_and_do_not_publish_empty(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);fig=p/'figures.json';studio=p/'studio.json';out=p/'out'
   fig.write_text(json.dumps(self.figures),encoding='utf-8');studio.write_text('[]')
   rows=mod.build(str(fig),str(studio),out)
   self.assertEqual(len(rows),1)
   self.assertTrue((out/'video'/'abcdefghijk'/'index.html').exists())
   self.assertTrue((out/'sitemap.xml').exists())
   fig.write_text('{"figures":[]}')
   with self.assertRaises(ValueError):mod.build(str(fig),str(studio),out)


 def test_every_page_has_context_and_profile_links(self):
  row=mod.normalize(self.figures)[0]
  page=mod.detail_page(row)
  self.assertIn('دربارهٔ این ویدئو',page)
  self.assertIn('موضوع اول',page)
  self.assertIn('https://pendar.io/figures/#/figure/person-a',page)
  self.assertIn('https://pendar.io/figures/#/figure/person-b',page)
  self.assertIn('رسانه و منبع انتشار',page)
  self.assertIn('منبع اصلی ویدئو',page)
  self.assertIn('schema.org',page)
 def test_source_media_is_linked_only_when_explicit_and_safe(self):
  self.figures['figures'][0]['youtube_videos'][0].update({
   'channel_name':'رسانه آزمایشی',
   'channel_url':'https://www.youtube.com/@example',
   'description_fa':'توضیح واقعی منتشرشده در منبع'})
  row=mod.normalize(self.figures)[0]
  page=mod.detail_page(row)
  self.assertIn('رسانه آزمایشی',page)
  self.assertIn('https://www.youtube.com/@example',page)
  self.assertIn('توضیح واقعی منتشرشده در منبع',page)
  self.assertNotIn('این صفحه به ویدئوی',page)
  self.assertEqual(mod.safe_channel_url('https://evil.example/@example'),'')
  self.assertEqual(mod.safe_channel_url('javascript:alert(1)'),'')


 def test_channel_one_is_media_not_a_person(self):
  self.figures['figures'].append({
   'handle':'source-channel-one-tv',
   'name_fa':'شبکه یک (Channel One TV)',
   'role_fa':'شبکه تلویزیونی و رسانه',
   'directory':False,
   'youtube_videos':[{'id':'abcdefghijk','url':'https://www.youtube.com/watch?v=abcdefghijk','title':'گفتگو','channel_url':'https://www.youtube.com/@ChanelOneTVIranian'}]
  })
  rows=mod.normalize(self.figures)
  self.assertEqual(len(rows),1)
  self.assertFalse(any(p['handle']=='source-channel-one-tv' for p in rows[0]['people']))
  self.assertEqual(rows[0]['media'][0]['name_fa'],'شبکه یک (Channel One TV)')
  page=mod.detail_page(rows[0])
  self.assertIn('رسانه و منبع انتشار',page)
  self.assertIn('شبکه یک (Channel One TV)',page)
  self.assertNotIn('figure/source-channel-one-tv',page)
 def test_specific_video_host_and_guest(self):
  extra={'abcdefghijk':[{'name_fa':'محمد منظرپور','role':'host','handle':'mohammad-manzarpour'},
                         {'name_fa':'بهمن جلدی','role':'guest','handle':'bahman-jeldi'}]}
  row=mod.normalize(self.figures,credits=extra)[0]
  page=mod.detail_page(row)
  self.assertIn('میزبان برنامه',page)
  self.assertIn('مهمان برنامه',page)
  self.assertIn('محمد منظرپور',page)
  self.assertIn('بهمن جلدی',page)
  self.assertIn('https://pendar.io/figures/#/figure/mohammad-manzarpour',page)
  self.assertIn('https://pendar.io/figures/#/figure/bahman-jeldi',page)
  self.assertEqual(mod.normalize(self.figures)[0]['credits'],[])

if __name__=='__main__':unittest.main()
