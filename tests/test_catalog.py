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

if __name__=='__main__':unittest.main()
