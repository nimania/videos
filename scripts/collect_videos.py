#!/usr/bin/env python3
"""Independent YouTube RSS discovery for Nimania Videos.

No Pendar read or import. The previous published Videos snapshot is the
append-only baseline. Missing feeds NEVER delete existing videos.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OWN_ARCHIVE="https://nimania.github.io/videos/data/videos.json"
VID=re.compile(r"^[A-Za-z0-9_-]{11}$")
CHANNEL=re.compile(r"^UC[A-Za-z0-9_-]{22}$")
ATOM={"atom":"http://www.w3.org/2005/Atom",
      "yt":"http://www.youtube.com/xml/schemas/2015",
      "media":"http://search.yahoo.com/mrss/"}

def fetch(url, limit=4_000_000, timeout=24):
    req=urllib.request.Request(url,headers={
        "User-Agent":"Mozilla/5.0 (compatible; NimaniaVideos/2.0)",
        "Accept":"application/json, application/atom+xml, text/html"})
    with urllib.request.urlopen(req,timeout=timeout) as response:
        if response.status!=200:raise ValueError("HTTP "+str(response.status))
        raw=response.read(limit+1)
        if len(raw)>limit:raise ValueError("Feed too large")
        return raw

def json_file(value):
    if str(value).startswith("https://"):return json.loads(fetch(value,28_000_000))
    return json.loads(Path(value).read_text(encoding="utf-8"))

def channel_id(url):
    match=re.search(r"/channel/(UC[A-Za-z0-9_-]{22})(?:/|$|\?)",url)
    if match:return match[1]
    raw=fetch(url.split("?")[0],limit=3_000_000).decode("utf-8","replace")
    for pattern in (
        r'"channelId"\s*:\s*"(UC[A-Za-z0-9_-]{22})"',
        r'"externalId"\s*:\s*"(UC[A-Za-z0-9_-]{22})"',
        r'itemprop="channelId"\s+content="(UC[A-Za-z0-9_-]{22})"',
        r'www\.youtube\.com/channel/(UC[A-Za-z0-9_-]{22})'):
        m=re.search(pattern,raw)
        if m:return m[1]
    raise ValueError("Channel ID could not be resolved")

def feed_entries(raw):
    xml=ET.fromstring(raw)
    records=[]
    for e in xml.findall("atom:entry",ATOM):
        vid=e.findtext("yt:videoId",default="",namespaces=ATOM)
        if not VID.fullmatch(vid):continue
        title=(e.findtext("atom:title",default="",namespaces=ATOM) or "").strip()[:360]
        date=(e.findtext("atom:published",default="",namespaces=ATOM) or "").strip()[:35]
        if not title:continue
        records.append({"id":vid,"title":title,"published_at":date,
                        "url":"https://www.youtube.com/watch?v="+vid,
                        "thumbnail":"https://i.ytimg.com/vi/"+vid+"/hqdefault.jpg"})
    return records

def norm(s):
    return re.sub(r"\s+"," ",str(s or "").replace("ي","ی").replace("ك","ک").replace("\u200c"," ")).strip().casefold()

def name_in_title(name,title):
    term=norm(name)
    if len(term)<5:return False
    value=norm(title)
    # require non-letter boundaries so that names aren't matched as substrings of words
    return bool(re.search(r"(?<![\w])"+re.escape(term)+r"(?![\w])",value))

def blank(entry):
    return {"id":entry["id"],"url":entry["url"],"title":entry["title"],
            "published_at":entry["published_at"],"thumbnail":entry["thumbnail"],
            "source_type":"official","topic_fa":"","summary_fa":"","recap_fa":"",
            "channel_name":"","channel_url":"","studio_id":"","people":[],"media":[],
            "credits":[],"related_links":[]}

def add_person(row,source):
    people=row.setdefault("people",[])
    if not any(x.get("handle","").lower()==source["handle"].lower() for x in people):
        people.append({"handle":source["handle"],"name_fa":source["name_fa"],"avatar":""})

def add_media(row,source):
    media=row.setdefault("media",[])
    if not any(x.get("handle","").lower()==source["handle"].lower() for x in media):
        media.append({"handle":source["handle"],"name_fa":source["name_fa"],
                      "url":source.get("channel_url","")})
    if not row.get("channel_url"):
        row["channel_url"]=source.get("channel_url","")
        row["channel_name"]=source["name_fa"]

def merge_snapshot(previous,discovered,sources,shared_hosts):
    if not isinstance(previous,dict) or not isinstance(previous.get("videos"),list):
        raise ValueError("Missing prior independent Videos snapshot")
    by_id={}
    for v in previous["videos"]:
        if isinstance(v,dict) and VID.fullmatch(str(v.get("id") or "")):
            by_id[v["id"]]=dict(v)
    count_before=len(by_id)
    by_handle={x["handle"]:x for x in sources}
    candidates=[x for x in sources if x.get("kind")=="person"]
    media_by_url={x["channel_url"].rstrip("/").casefold():x for x in sources if x.get("kind")=="media"}
    created=0
    for url,entries in discovered.items():
        owner=next((x for x in sources if x.get("channel_url","").rstrip("/").casefold()==url.rstrip("/").casefold()),None)
        host=media_by_url.get(url.rstrip("/").casefold())
        is_shared=url in shared_hosts
        for entry in entries:
            vid=entry["id"]
            if not VID.fullmatch(vid):continue
            row=by_id.get(vid)
            if row is None:
                row=blank(entry);by_id[vid]=row;created+=1
            else:
                # Keep editorial text, relationships, and the earlier publisher metadata.
                for k in ("people","media","credits","related_links"):
                    if not isinstance(row.get(k),list):row[k]=[]
                if not row.get("title"):row["title"]=entry["title"]
                if not row.get("thumbnail"):row["thumbnail"]=entry["thumbnail"]
                if entry["published_at"]>str(row.get("published_at") or ""):
                    row["published_at"]=entry["published_at"]
            if owner:
                if owner["kind"]=="media":add_media(row,owner)
                else:add_person(row,owner)
            if host:add_media(row,host)
            if is_shared:
                for person in candidates:
                    if name_in_title(person["name_fa"],entry["title"]) or any(name_in_title(a,entry["title"]) for a in person.get("aliases",[])):
                        add_person(row,person)
                        if owner is None or owner["kind"]=="media":row["source_type"]="hosted"
    if len(by_id)<count_before:raise ValueError("Discovery would shrink archive")
    result=sorted(by_id.values(),key=lambda v:(str(v.get("published_at") or ""),v["id"]),reverse=True)
    return result,created

def collect(previous,sources,reader=None,max_workers=10):
    """reader(source URL) -> Atom entries. Inject a stub for offline tests."""
    registry=sources.get("sources") or []
    shared=sources.get("shared_hosts") or []
    if not registry:raise ValueError("Empty curated registry")
    urls=list(dict.fromkeys(
        [x["channel_url"] for x in registry if x.get("channel_url")] + shared))
    discovered={}
    def scan(url):
        cid=channel_id(url) if reader is None else url
        return reader(url) if reader else feed_entries(fetch("https://www.youtube.com/feeds/videos.xml?channel_id="+cid,limit=1_000_000))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        future_map={ex.submit(scan,url):url for url in urls}
        for future in concurrent.futures.as_completed(future_map):
            url=future_map[future]
            try:
                entries=future.result()
                if entries:discovered[url]=entries
            except Exception as exc:
                print("Source unavailable (keeping existing): "+url+" ("+type(exc).__name__+")",file=sys.stderr)
    rows,created=merge_snapshot(previous,discovered,registry,shared)
    return rows,{"previous":len(previous["videos"]),"total":len(rows),"new":created,
                 "checked":len(urls),"responded":len(discovered)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--previous",default=OWN_ARCHIVE)
    p.add_argument("--sources",default=str(ROOT/"data"/"sources.json"))
    p.add_argument("--out",default="/tmp/nimania-video-owned.json")
    p.add_argument("--min-baseline",type=int,default=500)
    args=p.parse_args()
    previous=json_file(args.previous)
    count=len(previous.get("videos",[]))
    if count<args.min_baseline:raise SystemExit("Refusing migration: baseline has only "+str(count)+" videos")
    sources=json_file(args.sources)
    videos,stats=collect(previous,sources)
    if len(videos)<count:raise SystemExit("Refusing shrinkage")
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"schema_version":2,"generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
        "source":"Independent Nimania Videos YouTube registry and feeds",
        "videos":videos,"discovery_stats":stats},ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print("Independent video discovery:",stats)

if __name__=="__main__":main()
