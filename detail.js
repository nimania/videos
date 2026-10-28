/* Pre-generated detail has the title, embed, source and SEO; this adds cross-site links. */
(()=>{'use strict';const m=location.pathname.match(/\/videos\/video\/([A-Za-z0-9_-]{11})\/?$/);if(!m)return;const id=m[1],el=document.getElementById('detail-dynamic');if(!el)return;
 const esc=s=>String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
 fetch('/videos/data/videos.json').then(r=>{if(!r.ok)throw Error('Missing archive');return r.json()}).then(d=>{
  const v=(d.videos||[]).find(x=>x.id===id);if(!v)return;
  const links=[{title:'ویدئوی اصلی در یوتیوب',url:v.url}];
  if(v.recap_fa)links.push({title:'متن جان کلام در پندار',url:'https://pendar.io/statement/youtube-'+encodeURIComponent(id)+'/'});
  if(v.studio_id)links.push({title:'نسخهٔ آمادهٔ ضبط',url:'https://pendar.io/studio-recap/'+encodeURIComponent(v.studio_id)+'/'});
  for(const l of v.related_links||[]){if(l&&/^https:\/\/(pendar\.io|nimania\.github\.io)\//.test(l.url||''))links.push(l)}
  const people=(v.people||[]).filter(p=>/^[a-z0-9._-]{2,90}$/i.test(String(p.handle||''))).map(p=>'<a href="https://pendar.io/figure/'+encodeURIComponent(p.handle)+'/">'+esc(p.name_fa||p.handle)+'</a>').join('، ');
  el.innerHTML=(v.summary_fa||v.recap_fa?'<section class="detail-summary"><h2>دربارهٔ این ویدئو</h2><p>'+esc(v.summary_fa||v.recap_fa)+'</p></section>':'')+(people?'<div class="detail-people">چهره‌ها در پندار: '+people+'</div>':'')+'<div class="detail-links">'+links.filter(l=>l.url).map(l=>'<a href="'+esc(l.url)+'" target="_blank" rel="noopener noreferrer">'+esc(l.title||l.name)+'</a>').join('')+'</div>';
 }).catch(()=>{el.innerHTML='<p class="error">اطلاعات تکمیلی در دسترس نیست؛ ویدئو را از پیوند منبع اصلی مشاهده کنید.</p>'});
})();