/* Standalone archive: reads its own build snapshot, not Pendar at runtime. */
(() => {
 'use strict';
 const ROOT='/videos/', $=id=>document.getElementById(id);
 const esc=x=>String(x==null?'':x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const fa=n=>Number(n||0).toLocaleString('fa-IR');
 const date=s=>{let d=new Date(s);return Number.isFinite(d.getTime())?new Intl.DateTimeFormat('fa-IR',{year:'numeric',month:'long',day:'numeric',timeZone:'Asia/Tehran'}).format(d):''};
 const isId=x=>/^[A-Za-z0-9_-]{11}$/.test(String(x||''));
 const safeImage=u=>/^https:\/\/(?:i\.ytimg\.com|img\.youtube\.com|pendar\.io|nimania\.github\.io)\//.test(String(u||''))?u:'';
 let videos=[],filter='all',page=1,query='';const size=24;
 function card(v){
  const image=safeImage(v.thumbnail)||(isId(v.id)?'https://i.ytimg.com/vi/'+v.id+'/hqdefault.jpg':'');
  const link=ROOT+'video/'+encodeURIComponent(v.id)+'/';
  return '<article class="card"><a href="'+esc(link)+'"><span class="thumb">'+(image?'<img src="'+esc(image)+'" alt="" loading="lazy" onerror="this.remove()">':'')+'<span class="play">▶</span></span></a><div class="card-body"><a class="card-title" href="'+esc(link)+'">'+esc(v.title)+'</a><div class="card-meta">'+esc(date(v.published_at))+' · '+esc((v.people||[]).map(p=>p.name_fa).filter(Boolean).slice(0,2).join('، '))+'</div><div class="tags">'+(v.recap_fa?'<span>جان کلام</span>':'')+(v.source_type==='hosted'?'<span>حضور در برنامه</span>':'<span>ویدئو</span>')+'</div></div></article>';
 }
 function render(){
  const matches=videos.filter(v=>(filter!=='recaps'||Boolean(v.recap_fa))&&(!query||[v.title,v.topic_fa,...(v.people||[]).map(p=>p.name_fa)].join(' ').toLocaleLowerCase('fa').includes(query)));
  const pages=Math.max(1,Math.ceil(matches.length/size));page=Math.min(page,pages);
  $('status').textContent=fa(matches.length)+' ویدئو در آرشیو';
  $('video-grid').innerHTML=matches.length?matches.slice((page-1)*size,page*size).map(card).join(''):'<p class="empty">ویدئویی مطابق این جست‌وجو پیدا نشد.</p>';
  let nav=$('pagination');nav.textContent='';if(pages<=1)return;
  const from=Math.max(1,Math.min(page-4,pages-8)),to=Math.min(pages,Math.max(9,page+4));
  for(let i=from;i<=to;i++){let b=document.createElement('button');b.type='button';b.textContent=fa(i);b.className=i===page?'selected':'';b.setAttribute('aria-label','صفحه '+fa(i));b.onclick=()=>{page=i;render();window.scrollTo({top:0,behavior:'smooth'})};nav.append(b)}
 }
 async function start(){
  if(new URLSearchParams(location.search).get('filter')==='recaps')filter='recaps';
  document.querySelectorAll('[data-filter]').forEach(b=>{b.classList.toggle('selected',b.dataset.filter===filter);b.onclick=()=>{filter=b.dataset.filter;page=1;history.replaceState(null,'',filter==='recaps'?'?filter=recaps':location.pathname);document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('selected',x===b));render()}});
  $('search').addEventListener('input',e=>{query=e.target.value.trim().toLocaleLowerCase('fa');page=1;render()});
  try{const r=await fetch(ROOT+'data/videos.json',{cache:'no-cache'});if(!r.ok)throw Error('HTTP '+r.status);let d=await r.json();if(!Array.isArray(d.videos))throw Error('Invalid archive');videos=d.videos.filter(x=>isId(x.id)).sort((a,b)=>String(b.published_at||'').localeCompare(String(a.published_at||'')));render()}
  catch(e){$('status').textContent='دریافت آرشیو ممکن نشد';$('video-grid').innerHTML='<p class="error">فایل دادهٔ سایت در دسترس نیست.</p>'}
 }start();
})();