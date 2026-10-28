import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('owned_collector',ROOT/'scripts'/'collect_videos.py')
collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
spec2=importlib.util.spec_from_file_location('owned_builder',ROOT/'scripts'/'build_catalog.py')
builder=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(builder)

BASE={'schema_version':1,'videos':[{
 'id':'abcdefghijk','url':'https://www.youtube.com/watch?v=abcdefghijk',
 'title':'ویدئوی قدیمی','published_at':'2026-10-01',
 'thumbnail':'https://i.ytimg.com/vi/abcdefghijk/hqdefault.jpg',
 'summary_fa':'متن تحریریه‌ای محفوظ','recap_fa':'',
 'media':[{'handle':'source-channel-one-tv','name_fa':'شبکه یک','url':'https://www.youtube.com/@ChanelOneTVIranian'}],
 'people':[],'credits':[],'related_links':[],'studio_id':'','source_type':'official'}]}
SOURCES={'sources':[
 {'handle':'source-channel-one-tv','name_fa':'شبکه یک','channel_url':'https://www.youtube.com/@ChanelOneTVIranian','kind':'media','aliases':[]},
 {'handle':'mohammad-manzarpour','name_fa':'محمد منظرپور','channel_url':'https://www.youtube.com/@Manzarpour','kind':'person','aliases':[]}],
 'shared_hosts':['https://www.youtube.com/@ChanelOneTVIranian']}
VIDEO={'id':'zyxwvutsrqp','title':'گفت‌وگو با محمد منظرپور','published_at':'2026-10-27',
       'url':'https://www.youtube.com/watch?v=zyxwvutsrqp',
       'thumbnail':'https://i.ytimg.com/vi/zyxwvutsrqp/hqdefault.jpg'}

class OwnedVideoTests(unittest.TestCase):
 def test_no_remote_pendar_dependency_and_preserved_baseline(self):
  rows,stats=collector.collect(BASE,SOURCES,reader=lambda url:[VIDEO] if 'ChanelOneTVIranian' in url else [],max_workers=2)
  self.assertEqual(stats['previous'],1)
  self.assertEqual(stats['new'],1)
  self.assertEqual(len(rows),2)
  old=next(x for x in rows if x['id']=='abcdefghijk')
  self.assertEqual(old['summary_fa'],'متن تحریریه‌ای محفوظ')
  new=next(x for x in rows if x['id']=='zyxwvutsrqp')
  self.assertEqual(new['media'][0]['handle'],'source-channel-one-tv')
  self.assertEqual(new['people'][0]['handle'],'mohammad-manzarpour')
 def test_feed_outage_cannot_erase_video_archive(self):
  rows,stats=collector.collect(BASE,SOURCES,reader=lambda _:[],max_workers=2)
  self.assertEqual(len(rows),1)
  self.assertEqual(stats['new'],0)
 def test_owned_production_page_and_pendar_export(self):
  rows,_=collector.collect(BASE,SOURCES,reader=lambda url:[VIDEO] if 'ChanelOneTVIranian' in url else [],max_workers=2)
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp); archive=root/'video-archive.json';out=root/'site'
   archive.write_text(json.dumps({'videos':rows}),encoding='utf-8')
   builder.build_owned(str(archive),out,credits={'zyxwvutsrqp':[{'name_fa':'بهمن جلدی','handle':'bahman-jeldi','role':'guest'}]})
   self.assertTrue((out/'video'/'zyxwvutsrqp'/'index.html').exists())
   self.assertTrue((out/'media'/'source-channel-one-tv'/'index.html').exists())
   exported=json.loads((out/'data'/'pendar-youtube-videos.json').read_text(encoding='utf-8'))
   self.assertTrue(any(v['handle']=='source-channel-one-tv' and v['id']=='zyxwvutsrqp' for v in exported))
   self.assertTrue(any(v['handle']=='bahman-jeldi' and v['id']=='zyxwvutsrqp' for v in exported))
 def test_strict_title_matching(self):
  self.assertTrue(collector.name_in_title('محمد منظرپور','گفت‌وگو با محمد منظرپور'))
  self.assertFalse(collector.name_in_title('محمد منظرپور','برنامه با محمد منظریان'))
  self.assertFalse(collector.name_in_title('آرش','برنامه با آرش'))
 def test_source_registry_is_not_empty(self):
  data=json.loads((ROOT/'data'/'sources.json').read_text(encoding='utf-8'))
  self.assertGreaterEqual(len(data['sources']),40)
  self.assertIn('source-channel-one-tv',[x['handle'] for x in data['sources']])

if __name__=='__main__':unittest.main()
