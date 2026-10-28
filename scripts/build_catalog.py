#!/usr/bin/env python3
"""Build independent Nimania Videos snapshot from Pendar's public video catalogue.

GitHub Pages readers see only local, prebuilt JSON; the source is never queried in
the browser. Failure of the source must never publish an empty video archive.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import shutil
import sys
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT=Path(__file__).resolve().parents[1]
SITE='https://nimania.github.io/videos/'
PENDAR='https://pendar.io/'
FIGURES=PENDAR+'data/figures.json'
STUDIO=PENDAR+'data/studio-recaps.json'
VIDEO_ID=re.compile(r'^[A-Za-z0-9_-]{11}$')
HANDLE=re.compile(r'^[A-Za-z0-9_.-]{2,90}$')
RELATION_PREFIXES=(PENDAR,'https://nimania.github.io/jan-kalam/',
                   'https://nimania.github.io/badbadak/',
                   'https://nimania.github.io/pishkhan/',SITE)

def read_json(src):
    if src.startswith('https://'):
        req=urllib.request.Request(src,headers={'User-Agent':'Nimania-Videos-Archive/1.0 (+https://nimania.github.io/videos/)', 'Accept':'application/json'})
        with urllib.request.urlopen(req,timeout=45) as res:
            if res.status!=200: raise ValueError('HTTP '+str(res.status))
            raw=res.read(32_000_001)
            if len(raw)>32_000_000: raise ValueError('Upstream archive exceeded size limit')
            return json.loads(raw)
    return json.loads(Path(src).read_text(encoding='utf-8'))

def youtube_id(value):
    value=str(value or '').strip()
    if value.startswith('youtube-'): value=value[8:]
    if VIDEO_ID.fullmatch(value): return value
    if not value.startswith('https://'): return ''
    u=urlparse(value);host=(u.hostname or '').lower()
    if host in ('youtube.com','www.youtube.com','m.youtube.com','youtube-nocookie.com','www.youtube-nocookie.com'):
        if u.path=='/watch': value=parse_qs(u.query).get('v',[''])[0]
        elif u.path.startswith(('/shorts/','/live/','/embed/')): value=u.path.split('/')[2]
        else: return ''
    elif host in ('youtu.be','www.youtu.be'): value=u.path.strip('/').split('/')[0]
    else: return ''
    return value if VIDEO_ID.fullmatch(value) else ''

def clean_text(value,cap=1200):
    return re.sub(r'\s+',' ',re.sub(r'[\u0000-\u001f\u007f]',' ',str(value or ''))).strip()[:cap]

def safe_image(value):
    value=str(value or '').strip();url=urlparse(value)
    if url.scheme=='https' and url.hostname in {'i.ytimg.com','img.youtube.com','pendar.io','nimania.github.io'}: return value
    if value.startswith('/') and not value.startswith('//') and '..' not in value:
        return PENDAR.rstrip('/')+value
    return ''

def safe_relations(value):
    if not isinstance(value,dict): return {}
    result={}
    for video,items in value.items():
        if not VIDEO_ID.fullmatch(video) or not isinstance(items,list): continue
        links=[]
        for item in items:
            if not isinstance(item,dict): continue
            url=str(item.get('url') or '')
            title=clean_text(item.get('title'),100)
            if title and len(url)<600 and any(url.startswith(p) for p in RELATION_PREFIXES):
                links.append({'url':url,'title':title})
        if links: result[video]=links[:10]
    return result

def normalize(figures,studio_rows=None,relationships=None):
    if not isinstance(figures,dict) or not isinstance(figures.get('figures'),list):
        raise ValueError('Source figures.json missing figures[]')
    relations=safe_relations(relationships or {})
    studio={}
    for r in studio_rows if isinstance(studio_rows,list) else []:
        if not isinstance(r,dict): continue
        vid=youtube_id(r.get('video_id') or r.get('url'))
        if vid and r.get('id'): studio[vid]=clean_text(r.get('id'),100)
    by_id={}
    for person in figures['figures']:
        if not isinstance(person,dict): continue
        handle=str(person.get('handle') or '')
        if not HANDLE.fullmatch(handle): continue
        name=clean_text(person.get('name_fa') or person.get('name') or handle,140)
        records=person.get('youtube_videos') if isinstance(person.get('youtube_videos'),list) else []
        for v in records:
            if not isinstance(v,dict): continue
            vid=youtube_id(v.get('id')) or youtube_id(v.get('url'))
            if not vid or not youtube_id(v.get('url')): continue
            title=clean_text(v.get('title_fa') or v.get('title'),360)
            if not title: continue
            date=str(v.get('published_at') or '')[:35]
            item=by_id.get(vid)
            if item is None:
                item={'id':vid,'url':'https://www.youtube.com/watch?v='+vid,
                      'title':title,'published_at':date,
                      'thumbnail':safe_image(v.get('thumbnail')) or 'https://i.ytimg.com/vi/'+vid+'/hqdefault.jpg',
                      'source_type':clean_text(v.get('source_type'),32),
                      'topic_fa':'','summary_fa':'','recap_fa':'',
                      'studio_id':studio.get(vid,''),'people':[],
                      'related_links':relations.get(vid,[])}
                by_id[vid]=item
            else:
                if date>item['published_at']: item['published_at']=date
                if item['source_type']=='hosted' and v.get('source_type')=='official': item['source_type']='official'
            if not item['recap_fa'] and v.get('recap_fa'):
                item['recap_fa']=clean_text(v.get('recap_fa'),1100)
                item['summary_fa']=clean_text(v.get('summary_fa') or v.get('recap_fa'),1900)
                item['topic_fa']=clean_text(v.get('topic_fa'),200)
            elif not item['summary_fa'] and v.get('summary_fa'):
                item['summary_fa']=clean_text(v.get('summary_fa'),1900)
            if not any(p['handle'].lower()==handle.lower() for p in item['people']):
                item['people'].append({'handle':handle,'name_fa':name,
                                       'avatar':safe_image(person.get('avatar'))})
    return sorted(by_id.values(),key=lambda x:(x['published_at'],x['id']),reverse=True)

def detail_page(v):
    vid=v['id']
    title=html.escape(v['title'],quote=True)
    description=html.escape((v.get('summary_fa') or 'ویدئو، منبع اصلی و پیوندهای معتبر مرتبط')[:155],quote=True)
    thumb=html.escape(v['thumbnail'],quote=True)
    original=html.escape(v['url'],quote=True)
    canonical=SITE+'video/'+vid+'/'
    metadata={'@context':'https://schema.org','@type':'VideoObject','name':v['title'],
              'description':v.get('summary_fa') or v['title'],
              'thumbnailUrl':v['thumbnail'],'url':canonical,
              'embedUrl':'https://www.youtube-nocookie.com/embed/'+vid}
    if re.match(r'^\d{4}-\d{2}-\d{2}',v['published_at']):
        metadata['uploadDate']=v['published_at']
    schema=json.dumps(metadata,ensure_ascii=False).replace('<','\\u003c')
    people=html.escape('، '.join(p['name_fa'] for p in v['people'][:4]))
    date=html.escape(v['published_at'][:10])
    return f"""<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{description}"><meta property="og:type" content="video.other"><meta property="og:title" content="{title}"><meta property="og:image" content="{thumb}"><link rel="canonical" href="{canonical}"><link rel="stylesheet" href="/videos/styles.css"><title>{title} | ویدئوها</title><script type="application/ld+json">{schema}</script></head>
<body><header class="masthead"><div class="wrap mast"><a class="mark" href="/videos/"><span class="mark-icon">▶</span><span>ویدئوها<small>آرشیو مستقل نیمانیا</small></span></a><nav><a href="/videos/">ویدئوها</a><a href="https://pendar.io/">پندار</a><a href="https://nimania.github.io/jan-kalam/">جان کلام</a><a href="https://nimania.github.io/badbadak/">بادبادک</a><a href="https://nimania.github.io/pishkhan/">پیشخوان کتاب</a></nav></div></header>
<main class="wrap"><article class="detail"><a class="back" href="/videos/">بازگشت به فهرست</a><span class="eyebrow">ویدئو · منبع اصلی</span><h1>{title}</h1><p class="meta">{date} · {people}</p><div class="player"><iframe src="https://www.youtube-nocookie.com/embed/{vid}" title="{title}" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="accelerometer; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div><p><a class="back" href="{original}" target="_blank" rel="noopener noreferrer">ویدئوی اصلی در یوتیوب</a></p><div id="detail-dynamic"></div></article></main>
<footer class="footer"><div class="wrap"><span>ویدئوها · نیمانیا</span><span>مالکیت ویدئو متعلق به ناشر اصلی است</span></div></footer><script src="/videos/detail.js" defer></script></body></html>"""

def build(figures_source,studio_source,out,allow_empty=False,relations=None):
    figures=read_json(figures_source)
    try: studio=read_json(studio_source)
    except Exception as e:
        print('Studio unavailable: '+str(e),file=sys.stderr)
        studio=[]
    rows=normalize(figures,studio,relations)
    if not rows and not allow_empty: raise ValueError('Refusing to publish an empty archive')
    out.mkdir(parents=True,exist_ok=True)
    for f in ('index.html','styles.css','app.js','detail.js','.nojekyll'):
        shutil.copy2(ROOT/f,out/f)
    (out/'data').mkdir(exist_ok=True)
    snapshot={'schema_version':1,'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),
              'source':'Pendar published figures snapshot','videos':rows}
    (out/'data'/'videos.json').write_text(json.dumps(snapshot,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    for v in rows:
        folder=out/'video'/v['id'];folder.mkdir(parents=True,exist_ok=True)
        (folder/'index.html').write_text(detail_page(v),encoding='utf-8')
    (out/'recaps').mkdir(exist_ok=True)
    (out/'recaps'/'index.html').write_text('<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=/videos/?filter=recaps"><link rel="canonical" href="'+SITE+'?filter=recaps"><title>جان کلام ویدئوها</title><a href="/videos/?filter=recaps">جان کلام ویدئوها</a></html>',encoding='utf-8')
    urls=[SITE,SITE+'recaps/']+[SITE+'video/'+v['id']+'/' for v in rows]
    (out/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+html.escape(url)+'</loc></url>' for url in urls)+'</urlset>',encoding='utf-8')
    (out/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+SITE+'sitemap.xml\n',encoding='utf-8')
    print('Videos build: '+str(len(rows))+' distinct videos, '+str(sum(bool(v['recap_fa']) for v in rows))+' with recap')
    return rows

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--figures',default=FIGURES)
    parser.add_argument('--studio',default=STUDIO)
    parser.add_argument('--out',type=Path,default=Path('site'))
    parser.add_argument('--allow-empty',action='store_true')
    args=parser.parse_args()
    relations=read_json(str(ROOT/'data'/'relations.json'))
    build(args.figures,args.studio,args.out,allow_empty=args.allow_empty,relations=relations)

if __name__=='__main__': main()
