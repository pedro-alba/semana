/* The prototype's pure utilities (specs/semana.html), with no state of their own.
   Text comes from i18n.js, in the active language. */
import {t,locale,ordinal} from './i18n.js';
const DAY=86400000;
const HL='rgba(238, 196, 120, 0.34)';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const civil=s=>new Date(s.slice(0,10)+'T12:00:00Z');
const dateKey=d=>d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
const today=()=>dateKey(new Date());
const addDays=(s,n)=>{const d=civil(s);d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10)};
const weekOf=s=>addDays(s,-((civil(s).getUTCDay()+6)%7));
const dayDiff=(a,b)=>Math.round((civil(b)-civil(a))/DAY);
const validDate=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&Number.isFinite(+civil(s))&&civil(s).toISOString().slice(0,10)===s;
const clone=v=>JSON.parse(JSON.stringify(v));
const dateFmt=(s,o)=>new Intl.DateTimeFormat(locale(),{...o,timeZone:'UTC'}).format(civil(s));
const fmt=s=>dateFmt(s,{day:'2-digit',month:'short'});
const weekday=s=>dateFmt(s,{weekday:'short'});
const monthShort=s=>dateFmt(s,{month:'short'});
const fmtDay=s=>dateFmt(s,{weekday:'short',day:'numeric',month:'short'});
const stamp=s=>new Date(s).toLocaleString(locale(),{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'});

/* List order: open before done; within each group, the order the user chose. */
function ordered(list){
  return [...list].sort((a,b)=>(a.progress===100)-(b.progress===100)||a.order-b.order||a.createdAt.localeCompare(b.createdAt)||a.id.localeCompare(b.id));
}

/* ===================== Calendar ===================== */
function occurrences(e,ws){
  const we=addDays(ws,7),duration=dayDiff(e.start,e.end),out=[];
  for(let d=addDays(ws,-duration);d<we;d=addDays(d,1)){
    if(d<e.start.slice(0,10)||(e.until&&d>e.until)||e.except?.includes(d))continue;
    const base=e.start.slice(0,10),match=e.repeat==='daily'||(e.repeat==='weekly'?dayDiff(base,d)%7===0:e.repeat==='monthly'?d.slice(8)===base.slice(8):d===base);
    if(!match)continue;
    const start=d+e.start.slice(10),end=addDays(d,duration)+e.end.slice(10);
    if(end>ws+'T00:00'&&start<we+'T00:00')out.push({...e,start,end,occurrence:d});
  }
  return out;
}
/* Recurrence in words (007): "Every day", "Every Tuesday", "Every month on the 15th", with ", until 12/15". */
function repeatText(e){
  if(!e.repeat||e.repeat==='none')return '';
  /* Portuguese long weekday names end in "-feira" (segunda-feira); the short form reads better here. */
  const d=e.start.slice(0,10),day=dateFmt(d,{weekday:'long'}).replace('-feira','');
  const base=e.repeat==='daily'?t('repeat.daily'):e.repeat==='weekly'?t([0,6].includes(civil(d).getUTCDay())?'repeat.weekly_weekend':'repeat.weekly',{day}):t('repeat.monthly',{nth:ordinal(Number(d.slice(8)))});
  const u=e.until;
  return base+(u?t('repeat.until',{date:dateFmt(u,u.slice(0,4)===d.slice(0,4)?{day:'2-digit',month:'2-digit'}:{day:'2-digit',month:'2-digit',year:'numeric'})}):'');
}
/* Occurrence date to show in search (006 R3): the next one from today; if the series ended, the last one. */
function nextOccurrence(e,today){
  const first=e.start.slice(0,10);
  if(e.repeat==='none'||first>=today)return first;
  for(let w=weekOf(today),end=addDays(w,371);w<end;w=addDays(w,7)){const o=occurrences(e,w).map(x=>x.occurrence).find(d=>d>=today&&d>=first);if(o)return o}
  if(!e.until)return first;
  for(let w=weekOf(e.until);w>=weekOf(first);w=addDays(w,-7)){const o=occurrences(e,w).map(x=>x.occurrence).filter(d=>d>=first&&d<=e.until).pop();if(o)return o}
  return first;
}
function layoutEvents(list){
  const groups=[];let group=[],end=-1;
  for(const item of [...list].sort((a,b)=>a.a-b.a||a.b-b.b)){if(item.a>=end&&group.length){groups.push(group);group=[];end=-1}group.push({...item});end=Math.max(end,item.b)}
  if(group.length)groups.push(group);
  return groups.flatMap(g=>{const lanes=[];for(const x of g){let lane=lanes.findIndex(v=>v<=x.a);if(lane<0)lane=lanes.length;lanes[lane]=x.b;x.lane=lane}return g.map(x=>({...x,columns:lanes.length}))});
}


/* ===================== Links ===================== */
/* Accepts web addresses, e-mail and file paths (Windows, network and macOS/Linux) and returns an href. */
const encPath=p=>p.split(/[\\/]/).map(encodeURIComponent).join('/');
function parseLink(raw){
  const s=String(raw||'').trim().replace(/^[\s"'“”‘’<]+|[\s"'“”‘’>]+$/g,'');
  if(!s)return {error:t('link.empty')};
  try{
    if(/^(https?|file):\/\//i.test(s)||/^mailto:/i.test(s))return {href:new URL(s).href};
    if(/^[a-z]:[\\/]/i.test(s))return {href:'file:///'+s[0].toUpperCase()+':/'+encPath(s.slice(3))};
    if(/^\\\\[^\\/]+[\\/]/.test(s))return {href:new URL('file://'+encPath(s.slice(2))).href};
    if(/^\/[^/]/.test(s))return {href:'file:///'+encPath(s.slice(1))};
    if(/^~[\\/]/.test(s))return {error:t('link.full_path')};
    if(/^[^\s@/]+@[^\s@/]+\.[a-z]{2,}$/i.test(s))return {href:'mailto:'+s};
    if(/^(www\.)?[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}(:\d+)?([/?#]\S*)?$/i.test(s))return {href:new URL('https://'+s).href};
  }catch(_){}
  return {error:t('link.unknown')};
}
const isFileLink=h=>/^file:/i.test(h||'');
function nativePath(href){
  try{
    const u=new URL(href),p=decodeURIComponent(u.pathname);
    if(u.host)return '\\\\'+u.host+p.replace(/\//g,'\\');
    if(/^\/[a-z]:/i.test(p))return p.slice(1).replace(/\//g,'\\');
    return p;
  }catch(_){return href}
}
function linkLabel(href){
  if(isFileLink(href))return nativePath(href);
  if(/^mailto:/i.test(href))return href.slice(7);
  try{const u=new URL(href);return (u.host+u.pathname+u.search).replace(/\/$/,'')}catch(_){return href}
}
const fileName=href=>{const p=nativePath(href).replace(/[\\/]+$/,'');return p.split(/[\\/]/).pop()||p};
/* Pasted text that is only an address or a file path becomes a link. */
function autoLink(text){
  const s=String(text||'').trim();
  if(!s||/[\r\n]/.test(s))return '';
  const body=/^"[^"]+"$/.test(s)?s.slice(1,-1):s;
  const ok=/^(https?:\/\/|file:\/\/|www\.)\S+$/i.test(body)||/^[a-z]:\\/i.test(body)||/^\\\\[^\\]+\\/.test(body)||/^\/(Users|home|Volumes|mnt|media)\/./.test(body);
  return ok?(parseLink(body).href||''):'';
}

/* ===================== Rich text sanitizing ===================== */
/* Output limited to: p, h2, h3, ul, ol, li, strong, em, mark, a[href http/https/mailto/file], br
   and img[src /api/images/<uuid>, width] (008). */
const IMG_SRC=/^\/api\/images\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const DROP_TAGS=new Set(['SCRIPT','STYLE','TEMPLATE','IFRAME','OBJECT','EMBED','META','LINK','TITLE','HEAD','NOSCRIPT','SVG','MATH','IMG','PICTURE','SOURCE','VIDEO','AUDIO','CANVAS','INPUT','BUTTON','SELECT','TEXTAREA','FORM','HR']);
const BLOCK_TAGS=new Set(['P','DIV','H1','H2','H3','H4','H5','H6','BLOCKQUOTE','PRE','SECTION','ARTICLE','HEADER','FOOTER','MAIN','ASIDE','NAV','FIGURE','FIGCAPTION','TABLE','THEAD','TBODY','TFOOT','TR','TD','TH','CAPTION','DL','DT','DD','ADDRESS','CENTER','DETAILS','SUMMARY']);
const BLOCK_SELECTOR=[...BLOCK_TAGS,'UL','OL','LI'].map(t=>t.toLowerCase()).join(',');
/* Backgrounds that do not count as highlight: transparent, white, gray or dark (copied page backgrounds). */
function clearColor(v){
  v=String(v||'').trim().toLowerCase();
  if(!v||['transparent','initial','inherit','unset','none','currentcolor','revert','white','black'].includes(v))return true;
  const m=v.match(/^rgba?\(([^)]*)\)$/);
  if(!m)return false;
  const p=m[1].split(/[\s,/]+/).filter(Boolean).map(parseFloat);
  if(p.length>=4&&p[3]===0)return true;
  const [r,g,b]=p,max=Math.max(r,g,b),min=Math.min(r,g,b),lum=(.2126*r+.7152*g+.0722*b)/255;
  if(min>=245)return true;
  if(lum<.25)return true;
  if(max-min<12&&lum<.9)return true;
  return false;
}
function nextFormat(el,f){
  const tag=el.tagName.toUpperCase(),st=el.style,g={...f};
  if(tag==='B'||tag==='STRONG')g.b=true;
  if(tag==='I'||tag==='EM')g.i=true;
  if(tag==='MARK')g.h=true;
  if(st){
    const w=st.fontWeight;
    if(w){const n=parseInt(w,10);if(w==='bold'||w==='bolder'||n>=600)g.b=true;else if(w==='normal'||w==='lighter'||(n>0&&n<600))g.b=false}
    const s=st.fontStyle;
    if(s==='italic'||s==='oblique')g.i=true;else if(s==='normal')g.i=false;
    const bg=st.backgroundColor;
    if(bg&&!BLOCK_TAGS.has(tag)&&!['UL','OL','LI'].includes(tag))g.h=!clearColor(bg);
  }
  if(tag==='A'){const href=(el.getAttribute('href')||'').trim();if(/^(https?:|mailto:|file:)/i.test(href))g.a=href}
  return g;
}
function sanitizeHTML(input){
  const doc=new DOMParser().parseFromString('<!doctype html><body>'+String(input||'')+'</body>','text/html');
  const mk=t=>doc.createElement(t),blocks=[];
  let cur=null,list=null,inLi=false;
  const target=()=>{if(cur)return cur;if(list){cur=mk('li');list.append(cur)}else{cur=mk('p');blocks.push(cur)}return cur};
  const text=(t,f)=>{if(!t)return;let n=doc.createTextNode(t);for(const [on,tag] of [[f.h,'mark'],[f.i,'em'],[f.b,'strong']])if(on){const w=mk(tag);w.append(n);n=w}if(f.a){const a=mk('a');a.setAttribute('href',f.a);a.append(n);n=a}target().append(n)};
  const walk=(node,f)=>{
    for(const n of [...node.childNodes]){
      if(n.nodeType===3){const t=n.data.replace(/[\t\n\r\f ]+/g,' ');if(!cur&&!t.trim())continue;text(t,f);continue}
      if(n.nodeType!==1)continue;
      const tag=n.tagName.toUpperCase();
      if(tag==='IMG'){
        const src=n.getAttribute('src')||'',w=n.getAttribute('width')||'';
        if(IMG_SRC.test(src)){const img=mk('img');img.setAttribute('src',src);if(/^\d+$/.test(w)&&+w>=16&&+w<=4000)img.setAttribute('width',w);target().append(img)}
        continue;
      }
      if(DROP_TAGS.has(tag))continue;
      const g=nextFormat(n,f);
      if(tag==='BR'){target().append(mk('br'));continue}
      if(tag==='UL'||tag==='OL'){if(inLi){walk(n,g);continue}cur=null;list=mk(tag.toLowerCase());blocks.push(list);walk(n,g);list=null;cur=null;continue}
      if(tag==='LI'){if(!list){list=mk('ul');blocks.push(list)}cur=mk('li');list.append(cur);const was=inLi;inLi=true;walk(n,g);inLi=was;cur=null;continue}
      if(BLOCK_TAGS.has(tag)){
        if(inLi){walk(n,g);continue}
        if(n.querySelector(BLOCK_SELECTOR)){cur=null;walk(n,g);cur=null;continue}
        list=null;cur=mk(/^H[12]$/.test(tag)?'h2':/^H[3-6]$/.test(tag)?'h3':'p');blocks.push(cur);walk(n,g);cur=null;continue;
      }
      walk(n,g);
    }
  };
  walk(doc.body,{b:false,i:false,h:false,a:''});
  const merge=el=>{let c=el.firstChild;while(c){const nx=c.nextSibling;if(nx&&c.nodeType===1&&nx.nodeType===1&&c.tagName===nx.tagName&&['STRONG','EM','MARK','A'].includes(c.tagName)&&(c.tagName!=='A'||c.getAttribute('href')===nx.getAttribute('href'))){while(nx.firstChild)c.append(nx.firstChild);nx.remove();continue}if(c.nodeType===1)merge(c);c=c.nextSibling}};
  const keep=[];
  for(const b of blocks){
    if(b.tagName==='UL'||b.tagName==='OL'){if(!b.children.length)continue;for(const li of b.children){if(!li.textContent.trim()&&!li.querySelector('br,img')){li.textContent='';li.append(mk('br'))}merge(li)}keep.push(b);continue}
    if(!b.textContent.trim()&&!b.querySelector('br,img')){b.textContent='';b.append(mk('br'))}
    merge(b);keep.push(b);
  }
  if(!keep.some(b=>b.textContent.trim()||b.tagName==='UL'||b.tagName==='OL'||b.querySelector('img')))return '';
  return keep.map(b=>b.outerHTML).join('');
}
/* In the editor, the highlight becomes a span with a background so the browser can toggle it. */
const toEditor=html=>{const c=sanitizeHTML(html);return c?c.replace(/<mark>/g,'<span style="background-color: '+HL+';">').replace(/<\/mark>/g,'</span>'):'<p><br></p>'};
const textToHtml=s=>{s=String(s||'');if(!s.trim())return '';return s.split(/\r?\n/).map(l=>l.trim()?'<p>'+esc(l)+'</p>':'<p><br></p>').join('')};
const plainText=html=>new DOMParser().parseFromString(String(html||''),'text/html').body.textContent||'';

/* ===================== Search (prototype, lines 879–881 and 1633–1671) ===================== */
/* Running text of a restricted HTML, with a space between blocks (used by search). */
const textOf=html=>plainText(String(html||'').replace(/<\/(p|h2|h3|li)>/gi,' </$1>').replace(/<br\s*\/?>/gi,' ')).replace(/\s+/g,' ').trim();
/* Lowercase and without accents, character by character, so positions stay aligned with the original text. */
const fold=s=>{let o='';for(let i=0;i<s.length;i++){const c=s[i],f=c.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();o+=f[0]||c}return o};
/* Searchable items: tasks (prototype format), week notes ({"week|project": html}) and events. */
function searchItems(tasks,notes,events=[],today=''){
  const items=tasks.map(x=>({kind:'task',id:x.id,t:x,title:x.title.trim()||t('task.untitled'),body:[textOf(x.description),...x.subtasks.map(s=>s.text)].filter(Boolean).join(' · '),week:x.week,projectId:x.projectId,at:x.lastActivity}));
  for(const [k,html] of Object.entries(notes)){const body=textOf(html);if(body)items.push({kind:'notes',key:k,title:t('notes.week'),body,week:k.slice(0,10),projectId:k.slice(11),at:''})}
  for(const e of events){const day=nextOccurrence(e,today);items.push({kind:'event',id:e.id,e,day,title:e.title.trim()||t('task.untitled'),body:[e.location,e.description].filter(Boolean).join(' · '),week:weekOf(day),projectId:e.projectId,at:''})}
  for(const it of items){it.ft=fold(it.title);it.fb=fold(it.body)}
  return items;
}
function rankSearch(items,q,currentWeek){
  const terms=fold(q).split(/\s+/).filter(Boolean);
  if(!terms.length)return {terms,recent:true,list:items.filter(it=>it.kind==='task'&&it.t.progress<100).sort((a,b)=>b.at.localeCompare(a.at)).slice(0,8)};
  const fq=terms.join(' '),out=[];
  for(const it of items){
    let score=0;
    for(const term of terms){const i=it.ft.indexOf(term);if(i>=0)score+=i===0?60:40;else if(it.fb.includes(term))score+=10;else{score=-1;break}}
    if(score<0)continue;
    if(it.ft===fq)score+=100;else if(it.ft.startsWith(fq))score+=50;
    if(it.week===currentWeek)score+=8;else if(it.week>currentWeek)score+=4;
    if(it.kind==='task'&&it.t.progress===100)score-=6;
    out.push({it,score});
  }
  out.sort((a,b)=>b.score-a.score||b.it.week.localeCompare(a.it.week)||b.it.at.localeCompare(a.it.at));
  return {terms,recent:false,list:out.slice(0,10).map(x=>x.it)};
}
function markTerms(text,terms){
  const f=fold(text),r=[];
  for(const t of terms){let i=f.indexOf(t);while(i>=0){r.push([i,i+t.length]);i=f.indexOf(t,i+t.length)}}
  if(!r.length)return esc(text);
  r.sort((a,b)=>a[0]-b[0]);const m=[];
  for(const x of r){const l=m[m.length-1];if(l&&x[0]<=l[1])l[1]=Math.max(l[1],x[1]);else m.push([...x])}
  let o='',p=0;for(const [a,b] of m){o+=esc(text.slice(p,a))+'<mark>'+esc(text.slice(a,b))+'</mark>';p=b}
  return o+esc(text.slice(p));
}
function snippetOf(it,terms){
  const need=it.kind==='notes'?terms:terms.filter(t=>!it.ft.includes(t));
  let idx=-1;for(const t of need){const i=it.fb.indexOf(t);if(i>=0&&(idx<0||i<idx))idx=i}
  if(idx<0)return it.kind==='notes'?esc(it.body.slice(0,110))+(it.body.length>110?'…':''):'';
  let a=Math.max(0,idx-48);const b=Math.min(it.body.length,idx+100);
  if(a>0){const sp=it.body.indexOf(' ',a);if(sp>=0&&sp<idx)a=sp+1}
  return (a>0?'…':'')+markTerms(it.body.slice(a,b),terms)+(b<it.body.length?'…':'');
}

/* ---------- Backup (feature 005): prototype conversion, copied without changing the logic ---------- */
function assignOrder(list){
  const groups={},has=t=>Number.isFinite(t.order);
  for(const t of list)if(t&&typeof t==='object')(groups[t.week+'|'+t.projectId]??=[]).push(t);
  for(const g of Object.values(groups)){
    if(g.every(has))continue;
    g.sort((a,b)=>(has(a)?0:1)-(has(b)?0:1)||(has(a)&&has(b)?a.order-b.order:0)||(!!b.important-!!a.important)||String(a.createdAt).localeCompare(String(b.createdAt))||String(a.id).localeCompare(String(b.id)));
    g.forEach((t,i)=>{t.order=i});
  }
}
function migrate(raw){
  if(!raw||typeof raw!=='object'||raw.version!==1)return raw;
  const isoOr=(v,f)=>typeof v==='string'&&Number.isFinite(Date.parse(v))?v:f;
  const idOk=v=>typeof v==='string'&&/^[a-zA-Z0-9_-]{1,124}$/.test(v);
  let n=0;
  const conv=t=>{
    if(!t||typeof t!=='object')return t;
    const created=isoOr(t.createdAt,new Date().toISOString()),subtasks=[],log=[];
    for(const r of Array.isArray(t.records)?t.records:[]){
      if(!r||typeof r!=='object')continue;
      const at=isoOr(r.at,created),rid=idOk(r.id)?r.id:'m'+(n++);
      if(r.kind==='system'){if(typeof r.text==='string'&&r.text.trim())log.push({id:rid,at,kind:'system',text:r.text.replace(' com urgência alta','')});continue}
      if(typeof r.text==='string'&&r.text.trim()&&r.text!=='Subtarefa criada.')log.push({id:'n_'+rid,at,kind:'note',text:r.text});
      if(r.next&&typeof r.next.text==='string'&&r.next.text.trim()){const done=r.next.state==='concluida';subtasks.push({id:rid,text:r.next.text.replace(/\s+/g,' ').trim().slice(0,300),done,createdAt:at,doneAt:done?isoOr(r.completedAt,at):''})}
    }
    let description=textToHtml(t.description);
    const links=(Array.isArray(t.links)?t.links:[]).filter(l=>l&&typeof l.url==='string'&&/^https?:\/\//i.test(l.url));
    if(links.length)description+='<p>'+links.map(l=>'<a href="'+esc(l.url)+'">'+esc(l.label||l.url)+'</a>').join('<br>')+'</p>';
    return {id:t.id,projectId:t.projectId,week:t.week,title:typeof t.title==='string'?t.title.slice(0,160):'',description:sanitizeHTML(description),important:t.urgency==='alta',due:'',progress:t.progress,createdAt:created,lastActivity:isoOr(t.lastActivity,created),carries:t.carries,subtasks,log};
  };
  const snapshots={};
  if(raw.snapshots&&typeof raw.snapshots==='object')for(const [k,v] of Object.entries(raw.snapshots))snapshots[k]=Array.isArray(v)?v.map(conv):v;
  return {version:2,demo:!!raw.demo,week:raw.week,projects:raw.projects,tasks:Array.isArray(raw.tasks)?raw.tasks.map(conv):raw.tasks,snapshots,
    events:Array.isArray(raw.events)?raw.events.map(e=>{if(!e||typeof e!=='object')return e;const {taskId,...rest}=e;return {...rest,until:rest.until||'',projectId:rest.projectId||'',description:rest.description||'',location:rest.location||''}}):raw.events};
}
/* Fills fields added in later versions (due date, order) and sanitizes the rich text. */
function normalize(s){
  if(!s||typeof s!=='object')return s;
  const fix=t=>{if(!t||typeof t!=='object')return;if(typeof t.description==='string')t.description=sanitizeHTML(t.description);if(t.due===undefined||t.due===null)t.due=''};
  if(s&&Array.isArray(s.tasks)){
    s.tasks.forEach(fix);assignOrder(s.tasks);
    if(s.snapshots&&typeof s.snapshots==='object')Object.values(s.snapshots).forEach(v=>{if(Array.isArray(v)){v.forEach(fix);assignOrder(v)}});
  }
  if(!s.notes||typeof s.notes!=='object'||Array.isArray(s.notes))s.notes={};
  for(const [k,v] of Object.entries(s.notes)){if(typeof v!=='string')continue;const c=sanitizeHTML(v);if(c)s.notes[k]=c;else delete s.notes[k]}
  return s;
}
function validateState(s){
  const text=x=>typeof x==='string',id=x=>text(x)&&/^[a-zA-Z0-9_-]{1,130}$/.test(x)&&!['constructor','__proto__','prototype'].includes(x),iso=x=>text(x)&&Number.isFinite(Date.parse(x)),dt=x=>text(x)&&validDate(x.slice(0,10))&&/^\d{4}-\d{2}-\d{2}T([01]\d|2[0-3]):[0-5]\d$/.test(x);
  if(!s||typeof s!=='object'||s.version!==2||!validDate(s.week)||weekOf(s.week)!==s.week||!Array.isArray(s.projects)||!s.projects.length||!Array.isArray(s.tasks)||!Array.isArray(s.events)||!s.snapshots||typeof s.snapshots!=='object'||Array.isArray(s.snapshots))return false;
  const pids=new Set(s.projects.map(p=>p&&p.id));
  if(pids.size!==s.projects.length||s.projects.some(p=>!p||!id(p.id)||!text(p.name)||!p.name.trim()||p.name.length>60))return false;
  if(!s.notes||typeof s.notes!=='object'||Array.isArray(s.notes)||Object.entries(s.notes).some(([k,v])=>{const m=/^(\d{4}-\d{2}-\d{2})\|([a-zA-Z0-9_-]{1,130})$/.exec(k);return !m||!validDate(m[1])||weekOf(m[1])!==m[1]||!pids.has(m[2])||!text(v)}))return false;
  const sub=x=>x&&id(x.id)&&text(x.text)&&x.text.trim()&&x.text.length<=300&&typeof x.done==='boolean'&&iso(x.createdAt)&&(x.done?iso(x.doneAt):x.doneAt==='');
  const log=x=>x&&id(x.id)&&iso(x.at)&&text(x.text)&&['system','note'].includes(x.kind);
  const task=t=>t&&id(t.id)&&pids.has(t.projectId)&&text(t.title)&&t.title.length<=160&&text(t.description)&&validDate(t.week)&&weekOf(t.week)===t.week&&Number.isInteger(t.progress)&&t.progress>=0&&t.progress<=100&&typeof t.important==='boolean'&&(t.due===''||validDate(t.due))&&Number.isFinite(t.order)&&Number.isInteger(t.carries)&&t.carries>=0&&iso(t.createdAt)&&iso(t.lastActivity)&&Array.isArray(t.subtasks)&&t.subtasks.every(sub)&&Array.isArray(t.log)&&t.log.every(log);
  if(!s.tasks.every(task)||new Set(s.tasks.map(t=>t.id)).size!==s.tasks.length)return false;
  if(Object.entries(s.snapshots).some(([k,v])=>!validDate(k)||weekOf(k)!==k||!Array.isArray(v)||!v.every(task)))return false;
  return s.events.every(e=>e&&id(e.id)&&text(e.title)&&e.title.trim()&&dt(e.start)&&dt(e.end)&&e.end>e.start&&dayDiff(e.start,e.end)<=31&&['none','weekly','monthly'].includes(e.repeat)&&(e.until===''||validDate(e.until))&&(e.projectId===''||pids.has(e.projectId))&&text(e.description)&&text(e.location)&&typeof e.allDay==='boolean');
}
/* Prototype v2 state → the app's backup file (005 data model). */
const taskFromPrototype=t=>({id:t.id,project_id:t.projectId,week:t.week,title:t.title,notes:t.description,
  important:t.important,progress:t.progress,position:t.order,weeks_open:t.carries+1,due:t.due||null,
  created_at:t.createdAt,updated_at:t.lastActivity,
  subtasks:t.subtasks.map(x=>({id:x.id,text:x.text,created_at:x.createdAt,done_at:x.done?x.doneAt:null})),
  log:t.log.map(l=>({id:l.id,at:l.at,kind:l.kind,text:l.text}))});
function fromPrototype(s){
  const now=new Date().toISOString();
  return {format:'semana-backup',version:1,processed_week:addDays(s.week,-7),
    projects:s.projects.map(p=>({id:p.id,name:p.name,created_at:now})),
    tasks:s.tasks.map(taskFromPrototype),
    notes:Object.entries(s.notes).filter(([,h])=>h).map(([k,html])=>{const [week,project_id]=k.split('|');return {project_id,week,html}}),
    events:s.events.map(e=>({id:e.id,project_id:e.projectId||null,title:e.title,start:e.start,end:e.end,all_day:e.allDay,
      repeat:e.repeat,until:e.until||null,location:e.location,description:e.description})),
    snapshots:Object.entries(s.snapshots).map(([week,ts])=>({week,tasks:ts.map(taskFromPrototype)}))};
}
/* File text → the app's backup, or null if it is not a recognized backup. */
function readBackup(text){
  try{
    const x=JSON.parse(text);
    if(x&&x.format==='semana-backup')return x;
    const s=normalize(migrate(x));
    return validateState(s)?fromPrototype(s):null;
  }catch(_){return null}
}
function backupSummary(b){
  const weeks=new Set([...(b.tasks||[]).map(t=>t.week),...(b.snapshots||[]).map(r=>r.week)]);
  return {projects:(b.projects||[]).length,tasks:(b.tasks||[]).length,events:(b.events||[]).length,weeks:weeks.size};
}

export {DAY,HL,esc,civil,dateKey,today,addDays,weekOf,dayDiff,validDate,clone,fmt,weekday,monthShort,fmtDay,stamp,ordered,occurrences,nextOccurrence,repeatText,layoutEvents,
  encPath,parseLink,isFileLink,nativePath,linkLabel,fileName,autoLink,
  DROP_TAGS,BLOCK_TAGS,BLOCK_SELECTOR,clearColor,nextFormat,sanitizeHTML,toEditor,textToHtml,plainText,
  textOf,fold,searchItems,rankSearch,markTerms,snippetOf,
  assignOrder,migrate,normalize,validateState,fromPrototype,readBackup,backupSummary};
