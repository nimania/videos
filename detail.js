/* Page explanation and primary cross-site links are pre-rendered.
   This optional enhancement adds curated links and more videos featuring the same figures. */
(()=>{'use strict';
 const m=location.pathname.match(/\/videos\/video\/([A-Za-z0-9_-]{11})\/?$/);
 if(!m)return;
 const id=m[1],el=document.getElementById('detail-dynamic');if(!el)return;
 const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const validURL=u=>{try{const x=new URL(u);return x.protocol==='https:'&&['pendar.io','nimania.github.io'].includes(x.hostname)}catch{return false}};
 fetch('/videos/data/videos.json').then(r=>{if(!r.ok)throw Error('Missing archive');return r.json()}).then(d=>{
  const all=Array.isArray(d.videos)?d.videos:[];
  const v=all.find(x=>x.id===id);if(!v)return;
  let sections=[];
  const links=[];
  if(v.recap_fa)links.push({title:'متن جان کلام در پندار',url:'https://pendar.io/statement/youtube-'+encodeURIComponent(id)+'/'});
  if(v.studio_id)links.push({title:'متن مرتبط در استودیوی پندار',url:'https://pendar.io/studio-recap/'+encodeURIComponent(v.studio_id)+'/'});
  for(const l of v.related_links||[])if(l&&validURL(l.url)&&l.title)links.push(l);
  if(links.length)sections.push('<section class="detail-context"><h2>متن‌ها و منابع مرتبط</h2><div class="detail-links">'+links.filter(l=>validURL(l.url)).map(l=>'<a href="'+esc(l.url)+'" target="_blank" rel="noopener noreferrer">'+esc(l.title)+'</a>').join('')+'</div></section>');
  const handles=new Set((v.people||[]).map(p=>String(p.handle||'').toLowerCase()).filter(Boolean));
  const mediaHandles=new Set((v.media||[]).map(p=>String(p.handle||'').toLowerCase()).filter(Boolean));
  if(handles.size||mediaHandles.size){
   const related=all.filter(x=>x.id!==id&&((x.people||[]).some(p=>handles.has(String(p.handle||'').toLowerCase()))||(x.media||[]).some(p=>mediaHandles.has(String(p.handle||'').toLowerCase()))))
    .sort((a,b)=>String(b.published_at||'').localeCompare(String(a.published_at||''))).slice(0,6);
   if(related.length){
    const cards=related.map(x=>'<a class="related-video" href="/videos/video/'+encodeURIComponent(x.id)+'/"><img src="https://i.ytimg.com/vi/'+encodeURIComponent(x.id)+'/mqdefault.jpg" alt="" loading="lazy"><span>'+esc(x.title)+'</span></a>').join('');
    sections.push('<section class="detail-context"><h2>ویدئوهای دیگر از این چهره‌ها یا رسانه</h2><div class="related-videos">'+cards+'</div></section>');
   }
  }
  el.innerHTML=sections.join('');
 }).catch(()=>{el.innerHTML='';/* Static descriptions and links remain readable. */});
})();
