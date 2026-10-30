/* Semana: the prototype's interface (specs/semana.html) wired to the API through data.js. */
import {DAY,HL,esc,addDays,weekOf,dayDiff,validDate,clone,fmt,weekday,monthShort,fmtDay,stamp,ordered,occurrences,repeatText,layoutEvents,fold,searchItems,rankSearch,markTerms,snippetOf,parseLink,isFileLink,nativePath,linkLabel,fileName,autoLink,clearColor,sanitizeHTML,toEditor,textToHtml,plainText,readBackup,backupSummary} from './pure.js';
import * as data from './data.js';
import {t,setLanguage,language} from './i18n.js';

/* ===================== Application ===================== */
const $=s=>document.querySelector(s);
const svg=p=>'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'+p+'</svg>';
const icons={
  prev:svg('<path d="m12 5-7 7 7 7M5 12h14"/>'),
  next:svg('<path d="m12 5 7 7-7 7M5 12h14"/>'),
  calendar:svg('<rect x="4" y="5" width="16" height="16" rx="2"/><path d="M16 3v4M8 3v4M4 11h16"/>'),
  today:svg('<path d="M3 10a9 9 0 1 1 2.6 8.4M3 4v6h6"/>'),
  profile:svg('<circle cx="12" cy="8" r="3.5"/><path d="M5 21v-2a7 7 0 0 1 14 0v2"/>'),
  trash:svg('<path d="M3 6h18M9 6V4h6v2M5 6l1 14h12l1-14M10 10v6M14 10v6"/>'),
  flag:svg('<path d="M5 21V4M5 4h12l-2.5 4.5L17 13H5"/>'),
  x:svg('<path d="M7 7l10 10M17 7 7 17"/>'),
  check:svg('<path d="m5.5 12.5 4 4 9-9.5"/>'),
  chevron:svg('<path d="m7 10 5 5 5-5"/>'),
  plus:svg('<path d="M12 5v14M5 12h14"/>'),
  mark:svg('<path d="m14.5 3.5 5 5-8 8h-5v-5z"/><path d="m11 7 5 5"/><path class="mark-line" d="M4 20.5h16" stroke-width="2.4"/>'),
  list:svg('<path d="M10 6h10M10 12h10M10 18h10"/><circle cx="5" cy="6" r="1.2" fill="currentColor" stroke="none"/><circle cx="5" cy="12" r="1.2" fill="currentColor" stroke="none"/><circle cx="5" cy="18" r="1.2" fill="currentColor" stroke="none"/>'),
  link:svg('<path d="M10 14a4.5 4.5 0 0 0 6.4 0l3.2-3.2a4.5 4.5 0 0 0-6.4-6.4l-1.1 1.1"/><path d="M14 10a4.5 4.5 0 0 0-6.4 0l-3.2 3.2a4.5 4.5 0 0 0 6.4 6.4l1.1-1.1"/>'),
  unlink:svg('<path d="M9.5 6.2 10.8 5a4.5 4.5 0 0 1 6.4 6.4l-1.3 1.3M8.1 11.3l-1.3 1.3a4.5 4.5 0 0 0 6.4 6.4l1.3-1.2"/><path d="M4 4l16 16"/>'),
  file:svg('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>'),
  due:svg('<circle cx="12" cy="13" r="7.5"/><path d="M12 9.5V13l2.4 1.8M5 4 2.8 6.2M19 4l2.2 2.2"/>'),
  external:svg('<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>'),
  go:svg('<path d="M7 17 17 7M9 7h8v8"/>'),
  sun:svg('<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6l1.4 1.4M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4"/>'),
  moon:svg('<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>'),
  monitor:svg('<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>'),
  search:svg('<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/>'),
  notes:svg('<rect x="5" y="3.5" width="14" height="17" rx="2"/><path d="M8.5 8.5h7M8.5 12h7M8.5 15.5h4"/>'),
  pencil:svg('<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m13.5 6.5 4 4"/>')
};

const sizeLabel=v=>t('fmt.size_'+v);

let S=null,account=null,startInfo=null,offset=0,project='',week='',pane=null,notice='',storage='';
let confirmTask=false,addingProject=false,ed=null,lastRange=null,notesTimer=0,titleTimer=0,suppressUntil=0,toastUndo=null,toastTimer=0,toolbarFrame=0;
let linkCtx=null,bubbleLink=null,gesture=null,scrollFrame=0,profileView='',profilePending=0,tickTimer=0,resetToken='';
let screen='tasks',filter='',draft=null,deleteEvent='',search=null;
const conflicts=new Map();

const opt=(v,l,s)=>'<option value="'+esc(v)+'"'+(v===s?' selected':'')+'>'+esc(l)+'</option>';
const btn=(act,label,id='',cls='',aria='',extra='')=>'<button type="button" data-act="'+act+'" data-id="'+esc(id)+'"'+(cls?' class="'+cls+'"':'')+(aria?' aria-label="'+esc(aria)+'" title="'+esc(aria)+'"':'')+(extra?' '+extra:'')+'>'+label+'</button>';
const field=(name,label,value='',type='text',extra='')=>'<label>'+label+'<input name="'+name+'" type="'+type+'" value="'+esc(value)+'" '+extra+'></label>';
const pname=id=>S.projects.find(p=>p.id===id)?.name||t('project.none');
const readOnly=()=>week<S.week;
const tasks=()=>readOnly()?(S.snapshots[week]||S.tasks.filter(x=>x.week===week)):S.tasks.filter(x=>x.week===week);
const projectTasks=()=>ordered(tasks().filter(x=>x.projectId===project));
const current=()=>pane?tasks().find(x=>x.id===pane.id)||null:null;
const editable=()=>{const x=current();return x&&!readOnly()?x:null};
const liveTask=id=>S.tasks.find(x=>x.id===id);
const openSubs=x=>x.subtasks.filter(s=>!s.done);
/* Moments by the server's clock (offset kept when opening), in the API format. */
const now=()=>new Date(Date.now()+offset).toISOString().replace(/\.\d{3}Z$/,'Z');
const touch=x=>{x.lastActivity=now()};
const titleOf=x=>x.title.trim()||t('task.untitled');
const cardFor=id=>document.querySelector('.task-card[data-id="'+CSS.escape(id)+'"]');
const isBlank=x=>!x.title.trim()&&!plainText(x.description).trim()&&!/<img/i.test(x.description)&&!x.subtasks.length&&x.progress===0&&!x.log.length&&!x.important&&!x.due;
const isMobile=()=>matchMedia('(max-width:760px)').matches;
const coarse=()=>matchMedia('(pointer: coarse)').matches;
const lastOrder=(w,p)=>S.tasks.reduce((m,x)=>x.week===w&&x.projectId===p?Math.max(m,x.order):m,-1);
function srSay(msg){const el=$('#sr-status');if(!el)return;el.textContent='';setTimeout(()=>{el.textContent=msg},40)}

/* ---------- Persistence: operations for the server and a local copy of the week ---------- */
const storageLabel=s=>t('storage.'+s.kind,{n:s.pending});
function setStorage(v){storage=v;const el=$('#storage');if(el)el.textContent=v}
data.onState(s=>setStorage(storageLabel(s)));
/* API task → prototype format, and back for the cache. */
const fromAPI=(x,p,w)=>({id:x.id,projectId:x.project_id??p,week:x.week??w,title:x.title,description:x.notes,
  important:!!x.important,progress:x.progress,order:x.position,createdAt:x.created_at,
  lastActivity:x.updated_at,carries:x.weeks_open-1,
  subtasks:x.subtasks.map(s=>({id:s.id,text:s.text,done:!!s.done_at,createdAt:s.created_at,doneAt:s.done_at||'',rev:s.text_rev})),
  log:x.log.map(l=>({id:l.id,at:l.at,kind:l.kind,text:l.text})),
  due:x.due||'',rev:{title:x.title_rev,notes:x.notes_rev}});
const toAPI=x=>({id:x.id,project_id:x.projectId,week:x.week,title:x.title,title_rev:x.rev.title,
  notes:x.description,notes_rev:x.rev.notes,important:x.important,progress:x.progress,position:x.order,
  weeks_open:x.carries+1,created_at:x.createdAt,updated_at:x.lastActivity,due:x.due||null,
  subtasks:x.subtasks.map(s=>({id:s.id,text:s.text,text_rev:s.rev,created_at:s.createdAt,done_at:s.done?s.doneAt:null})),
  log:x.log.map(l=>({id:l.id,at:l.at,kind:l.kind,text:l.text}))});
const stateOf=w=>w<S.week?'past':w===S.week?'current':'planning';
function applyWeek(p,w,r){
  const ts=r.tasks.map(x=>fromAPI(x,p,w)),k=w+'|'+p;
  if(r.state==='past'||w<S.week)S.snapshots[w]=(S.snapshots[w]||[]).filter(x=>x.projectId!==p).concat(ts);
  else S.tasks=S.tasks.filter(x=>!(x.week===w&&x.projectId===p)).concat(ts);
  S.notes[k]=r.notes.html;S.notesRev[k]=r.notes.rev;
}
async function load(p,w){const r=await data.week(p,w);if(S)applyWeek(p,w,r)}
/* The week's events and due dates, from every project (feature 002). */
const eventFromAPI=x=>({id:x.id,title:x.title,start:x.start,end:x.end,allDay:!!x.all_day,fullDay:!!x.fills_day,except:x.skipped||[],projectId:x.project_id||'',repeat:x.repeat||'none',until:x.until||'',location:x.location,description:x.description,rev:x.rev||0});
const eventToAPI=e=>({id:e.id,project_id:e.projectId||null,title:e.title,start:e.start,end:e.end,all_day:e.allDay,fills_day:!!(e.allDay&&e.fullDay),skipped:e.repeat==='none'?[]:e.except||[],repeat:e.repeat||'none',until:e.until||null,location:e.location,description:e.description,rev:e.rev||0});
const dueFromAPI=x=>({id:x.task_id,projectId:x.project_id,week:x.week,title:x.title,due:x.due,progress:x.progress,important:!!x.important});
const dueToAPI=d=>({task_id:d.id,project_id:d.projectId,week:d.week,title:d.title,due:d.due,progress:d.progress,important:d.important});
/* Offline and with no local copy, the agenda stays empty and the calendar says so (FR-041). */
async function loadAgenda(w,valid=()=>true){
  let r;
  try{r=await data.agenda(w)}catch(e){if(e.kind==='session')throw e;if(S&&valid()){S.events=[];S.dues=[];S.agendaWeek=null}return}
  if(!S||!valid())return;
  S.events=r.events.map(eventFromAPI);S.dues=r.dues.map(dueFromAPI);S.agendaWeek=w;
}
function storeAgenda(){
  if(!S||!S.agendaWeek)return;
  data.store('agenda|'+S.agendaWeek,{week:S.agendaWeek,events:S.events.map(eventToAPI),dues:S.dues.map(dueToAPI)}).catch(()=>{});
}
/* Keeps the due-date strip and "On the agenda" up to date with a task changed locally. */
function syncDue(x,removed=false){
  if(!S||!S.agendaWeek)return;
  const w=S.agendaWeek,inside=x.due&&x.due>=w&&x.due<addDays(w,7),late=w===S.week&&x.due&&x.due<w&&x.progress<100;
  S.dues=S.dues.filter(d=>d.id!==x.id);
  if(!removed&&(inside||late))S.dues.push({id:x.id,projectId:x.projectId,week:x.week,title:x.title,due:x.due,progress:x.progress,important:x.important});
  storeAgenda();
}
/* Writes the week and project to the cache, with the local changes (read when offline). */
function persist(w=week,p=project){
  if(!S||w<S.week)return;
  const k=w+'|'+p;
  data.store('week|'+p+'|'+w,{week:w,state:stateOf(w),tasks:S.tasks.filter(x=>x.week===w&&x.projectId===p).map(toAPI),notes:{html:S.notes[k]||'',rev:S.notesRev[k]||0}}).catch(()=>{});
}
const persistTask=x=>persist(x.week,x.projectId);
function storeStart(){if(startInfo)data.store('start',{...startInfo,account,projects:S.projects.map(p=>({id:p.id,name:p.name}))}).catch(()=>{})}

/* ---------- Page structure ---------- */
function headerHTML(){
  return '<header class="app-header"><button type="button" class="brand" data-act="home" aria-label="'+esc(t('header.brand_label'))+'" title="'+esc(t('header.brand_title'))+'">semana<span class="brand-dot">.</span></button>'
    +'<nav aria-label="'+esc(t('header.nav'))+'">'+btn('tasks',t('nav.tasks'),'','nav'+(screen==='tasks'?' active':''),'',screen==='tasks'?'aria-current="page"':'')+btn('calendar',t('nav.calendar'),'','nav'+(screen==='calendar'?' active':''),'',screen==='calendar'?'aria-current="page"':'')+'</nav>'
    +'<div class="header-right"><details class="menu profile-menu"><summary aria-label="'+esc(t('profile.label'))+'" title="'+esc(t('profile.label'))+'"><span class="profile-icon">'+icons.profile+'</span></summary><div class="menu-pop'+(profileView||backupFile?'':' prefs-pop')+'" id="profile-pop">'+profileHTML()+'</div></details></div></header>';
}
function profileHTML(){
  const head='<p class="profile-email">'+esc(account.email)+'</p>';
  if(profileView==='logout')return head+'<p role="alert">'+esc(t('profile.logout_pending',{n:profilePending}))+'</p>'+btn('logout-confirm',t('profile.logout_anyway'),'','danger')+btn('profile-back',t('common.cancel'),'','ghost');
  if(profileView==='delete')return head+'<form id="delete-form"><p>'+t('profile.delete_warning')+'</p>'+field('password',t('profile.confirm_password'),'','password','required autocomplete="current-password"')+'<p class="error" role="alert"></p><button class="danger">'+t('profile.delete_all')+'</button></form>'+btn('profile-back',t('common.cancel'),'','ghost');
  if(backupFile)return head+backupHTML();
  return head+prefsHTML()+'<p class="menu-label" id="pl-backup">'+t('backup.label')+'</p>'+backupHTML()+btn('logout',t('profile.logout'))+btn('delete-account',t('profile.delete'))
    +(startInfo?.source_url&&/^https:\/\//.test(startInfo.source_url)?'<p class="theme-note"><a href="'+esc(startInfo.source_url)+'" target="_blank" rel="noopener">'+t('profile.source')+'</a> · '+t('profile.license')+'</p>':'');
}
/* ---------- Backup (feature 005): export, and import replacing everything ---------- */
let backupFile=null,backupPending=0;
function backupHTML(){
  if(backupFile){
    const r=backupSummary(backupFile);
    return '<p>'+esc(t('backup.summary',{projects:t('count.projects',{n:r.projects}),tasks:t('count.tasks',{n:r.tasks}),events:t('count.events',{n:r.events}),weeks:t('count.weeks',{n:r.weeks})}))+'</p>'
      +'<p role="alert">'+esc(t('backup.replace_warning'))+(backupPending?' '+esc(t('backup.pending_discard',{n:backupPending})):'')+'</p>'
      +btn('import-confirm',t('backup.import'),'','danger')+btn('import-cancel',t('common.cancel'),'','ghost');
  }
  return btn('export',t('backup.export'))
    +btn('import',t('backup.import'))+'<input id="import" type="file" accept=".json,application/json" hidden><p class="theme-note">'+t('backup.note')+'</p>';
}
async function exportBackup(){
  flushEdits();await data.send();
  let r;
  try{if(await data.pending())throw {kind:'network'};r=await data.api('GET','/api/backup')}
  catch(e){if(e.kind==='session')return loginScreen(e);toast(t('backup.export_offline'));return}
  if(r.status!==200){toast(t('backup.export_failed'));return}
  const url=URL.createObjectURL(new Blob([JSON.stringify(r.json,null,2)],{type:'application/json'})),a=document.createElement('a');
  a.href=url;a.download='semana-backup-'+today()+'.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2500);
}
function invalidBackup(){backupFile=null;notice=t('backup.invalid');render()}
async function readFile(input){
  const f=input.files[0];input.value='';
  const b=f.size>50*1024*1024?null:readBackup(await f.text());
  if(!b)return invalidBackup();
  backupFile=b;backupPending=await data.pending();
  const menu=$('.profile-menu');if(menu)menu.open=true;
  drawProfile();$('#profile-pop .danger')?.focus();
}
async function importBackup(){
  let r;
  try{r=await data.api('POST','/api/backup',backupFile)}
  catch(e){if(e.kind==='session')return loginScreen(e);toast(t('backup.import_offline'));return}
  if(r.status===422)return invalidBackup();
  if(r.status!==200){toast(t('backup.import_failed'));return}
  backupFile=null;S=null;ed=null;pane=null;
  await data.clearAccount(account.id);
  await enter();
  notice=t('backup.imported');render();
}

function drawProfile(){const p=$('#profile-pop');if(!p)return;p.classList.toggle('prefs-pop',!profileView&&!backupFile);p.innerHTML=profileHTML()}

/* ---------- Appearance (feature 004): the prototype's panel; the logic lives in appearance.js ---------- */
const THEMES=['graphite','paper','ink'];
const MODES=[['light','sun'],['dark','moon'],['system','monitor']];
const FONTS=['theme','mono','sans','serif'];
const PALETTES=['classic','sunset','lavender','moss','traffic','neutral'];
const LANGUAGES=['auto','en','pt-BR'];
const PREF_KEY={theme:'theme','mode-pref':'mode',font:'font',palette:'palette'};
const pref=k=>document.documentElement.getAttribute('data-'+k);
function setPref(kind,value){
  const k=PREF_KEY[kind];
  if(!appearance.VALUES[k]?.includes(value))return;
  const p={...appearance.current(),[k]:value};
  appearance.apply(p);
  document.querySelectorAll('[data-pref="'+kind+'"]').forEach(b=>b.setAttribute('aria-checked',String(b.dataset.value===value)));
  if(ed){autosize(ed.title);sizeSubs();updateBubble()}
  data.enqueue({op:'account.appearance',...p});
}
const radio=(act,kind,value,checked,inner,cls,label)=>'<button type="button" role="radio" class="'+cls+'" data-act="'+act+'" data-pref="'+kind+'" data-value="'+value+'" aria-checked="'+checked+'"'+(label?' aria-label="'+esc(label)+'"':'')+'>'+inner+'</button>';
function prefsHTML(){
  const choice=(kind,value,inner,cls,label)=>radio('pref',kind,value,pref(kind)===value,inner,cls,label);
  return '<p class="menu-label" id="pl-theme">'+t('look.theme')+'</p><div class="theme-list" role="radiogroup" aria-labelledby="pl-theme">'
    +THEMES.map(id=>choice('theme',id,'<span class="swatch" data-theme="'+id+'" data-mode="'+pref('mode')+'" aria-hidden="true"><i class="sw-card"></i><i class="sw-line"></i><i class="sw-line short"></i><i class="sw-dot"></i><b>Aa</b></span><span><strong>'+t('theme.'+id)+'</strong><small>'+t('theme.'+id+'_desc')+'</small></span>','theme-opt')).join('')+'</div>'
    +'<p class="menu-label" id="pl-mode">'+t('look.mode')+'</p><div class="seg" role="radiogroup" aria-labelledby="pl-mode">'+MODES.map(([v,ic])=>choice('mode-pref',v,icons[ic]+'<span>'+t('mode.'+v)+'</span>','')).join('')+'</div>'
    +'<p class="menu-label" id="pl-font">'+t('look.font')+'</p><div class="font-grid" role="radiogroup" aria-labelledby="pl-font">'+FONTS.map(v=>choice('font',v,'<span class="aa" data-font-sample="'+v+'" aria-hidden="true">Aa</span><small>'+t('font.'+v)+'</small>','font-opt',t('font.'+v))).join('')+'</div>'
    +'<p class="menu-label" id="pl-pal">'+t('look.palette')+'</p><div class="pal-grid" role="radiogroup" aria-labelledby="pl-pal">'+PALETTES.map(v=>choice('palette',v,'<span class="pal-bar" data-palette="'+v+'" aria-hidden="true"></span><small>'+t('palette.'+v)+'</small>','pal-opt',t('palette.'+v))).join('')+'</div>'
    +'<p class="menu-label" id="pl-lang">'+t('lang.label')+'</p><div class="seg" role="radiogroup" aria-labelledby="pl-lang">'+LANGUAGES.map(v=>radio('language','language',v,account.language===v,'<span>'+t('lang.'+v)+'</span>','')).join('')+'</div>'
    +'<p class="theme-note">'+t('look.note')+'</p>';
}

/* ---------- Language: account setting, applied without reloading (keeps the open task and the caret) ---------- */
function setLanguagePref(value){
  if(!LANGUAGES.includes(value)||!account||account.language===value)return;
  account.language=value;storeStart();
  data.enqueue({op:'account.language',value});
  relabel();
}
/* Caret as character offsets inside the notes, to survive a redraw. */
function offsetsOf(root,r){const o=n=>{const x=document.createRange();x.selectNodeContents(root);x.setEnd(n[0],n[1]);return x.toString().length};return [o([r.startContainer,r.startOffset]),o([r.endContainer,r.endOffset])]}
function pointAt(root,n){const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);for(let x=w.nextNode();x;x=w.nextNode()){if(n<=x.length)return [x,n];n-=x.length}return null}
/* Applies the account's language; when the active language changes, redraws everything in it. */
function relabel(){
  document.querySelectorAll('[data-act="language"]').forEach(b=>b.setAttribute('aria-checked',String(b.dataset.value===account.language)));
  const before=language();setLanguage(account.language);
  if(!S||language()===before)return;
  storage=storageLabel(data.state());
  const caret=ed&&!ed.read&&lastRange&&ed.notes.contains(lastRange.commonAncestorContainer)?offsetsOf(ed.notes,lastRange):null;
  const menu=$('.profile-menu')?.open;
  render();
  if(caret&&ed){const a=pointAt(ed.notes,caret[0]),b=pointAt(ed.notes,caret[1]);if(a&&b){lastRange=document.createRange();lastRange.setStart(...a);lastRange.setEnd(...b)}}
  if(menu){const m=$('.profile-menu');m.open=true;m.querySelector('[data-act="language"][aria-checked="true"]')?.focus()}
}

const weekBtn=(act,label)=>'<button type="button" data-act="'+act+'" class="week-button" aria-label="'+esc(label)+'" title="'+esc(label)+'">'+icons[act]+'</button>';
function toolbarHTML(){
  const cal=screen==='calendar',selected=cal?filter:project;
  const control=addingProject&&!cal
    ?'<form id="project-form" class="project-new"><input name="name" placeholder="'+esc(t('project.name'))+'" maxlength="60" required aria-label="'+esc(t('project.new_name'))+'" autocomplete="off"><button class="icon-btn" aria-label="'+esc(t('project.create'))+'" title="'+esc(t('project.create'))+'">'+icons.check+'</button>'+btn('cancel-project',icons.x,'','icon-btn',t('common.cancel'))+'</form>'
    :'<div class="project-row"><select id="project" aria-label="'+esc(cal?t('project.filter'):t('project.label'))+'">'+(cal?opt('',t('project.all'),filter):'')+S.projects.map(p=>opt(p.id,p.name,selected)).join('')+'</select>'+(cal?'':btn('new-project',icons.plus,'','icon-btn',t('project.create')))+'</div>';
  const st=stateOf(week);
  return '<div class="toolbar"><div class="project-selector"><span class="selector-label" aria-hidden="true">'+(cal?t('toolbar.visibility'):t('toolbar.project'))+'</span>'+control+'</div>'
    +'<div class="week-meta">'+(st==='current'?'':'<span class="eyebrow">'+(st==='past'?t('toolbar.past'):t('toolbar.planning'))+'</span>')+'<strong>'+fmt(week)+' <em>—</em> '+fmt(addDays(week,6))+'</strong></div>'
    +'<div class="week-controls" role="group" aria-label="'+esc(t('toolbar.weeks'))+'">'+weekBtn('prev',t('toolbar.prev'))+weekBtn('next',t('toolbar.next'))
    +'<details class="week-picker"><summary class="week-button" aria-label="'+esc(t('toolbar.pick'))+'" title="'+esc(t('toolbar.pick'))+'">'+icons.calendar+'</summary><label>'+t('toolbar.go_to')+'<input type="date" id="week" value="'+week+'"></label></details>'
    +weekBtn('today',cal?t('toolbar.back_current'):t('toolbar.current'))+'</div></div>';
}
const noticeHTML=()=>notice?'<div class="notice" role="status"><span>'+esc(notice)+'</span>'+btn('dismiss',icons.x,'','icon-btn',t('common.close_notice'))+'</div>':'';
function render(){
  detachEditor();
  if(!S.projects.some(p=>p.id===project))project=S.projects[0].id;
  const main=screen==='calendar'?'<main id="calendar" class="calendar-page"></main>':'<div class="workspace"><aside class="sidebar" aria-label="'+esc(t('nav.tasks'))+'"><div class="list-heading"><h2>'+t('nav.tasks')+' <span class="count" id="task-count">0</span></h2><div class="list-actions">'+btn('search',icons.search,'','icon-btn search-btn',t('search.button'))+btn('new-task',t('task.new'),'','primary')+'</div></div><div id="task-list"></div><div class="progress-legend" id="legend"></div></aside><main id="detail"></main></div>';
  $('#app').innerHTML=headerHTML()+toolbarHTML()+noticeHTML()+main
    +'<footer><span id="storage">'+esc(storage)+'</span><em>'+t('footer.motto')+'</em></footer>';
  if(screen==='calendar')drawCalendar();else{drawList();drawDetail()}
}
function drawToolbar(){const el=$('.toolbar');if(el)el.outerHTML=toolbarHTML()}

/* ---------- Task list ---------- */
/* Due date state relative to today, in the account's time zone (the due date does not depend on the task's week). */
function dueState(x){
  if(!x.due)return '';
  if(x.progress===100)return 'done';
  const td=today();
  if(x.due<td)return 'overdue';
  if(x.due===td)return 'today';
  if(x.due===addDays(td,1))return 'tomorrow';
  return weekOf(x.due)===weekOf(td)?'week':'later';
}
function dueShort(x){const st=dueState(x);return st&&st!=='done'?t('due.short_'+st,{date:fmt(x.due),day:weekday(x.due)}):''}
function cardSubHTML(x){
  if(x.progress===100)return t('task.done');
  const n=openSubs(x).length,parts=[],st=dueState(x);
  if(x.carries)parts.push(esc(t('task.carried',{n:x.carries+1})));
  if(st)parts.push('<span class="card-due'+(st==='overdue'?' overdue':'')+'">'+esc(dueShort(x))+'</span>');
  if(n)parts.push(esc(t('count.subtasks',{n})));
  return parts.join(' · ');
}
function cardHTML(x,i){
  const sel=pane?.id===x.id,title=x.title.trim(),read=readOnly();
  return '<button type="button" class="task-card pc'+(sel?' selected':'')+'" data-act="task" data-id="'+esc(x.id)+'" aria-pressed="'+sel+'" style="--p:'+x.progress+'"'+(sel?' title="'+esc(t('card.click_again'))+'"':'')+'>'
    +'<span class="card-index" aria-hidden="true">'+esc(t('card.number',{n:String(i+1).padStart(2,'0')}))+'</span><span class="card-title'+(title?'':' untitled')+'">'+esc(title||t('task.untitled'))+'</span><span class="card-sub">'+cardSubHTML(x)+'</span>'
    +(x.important?'<span class="card-flag" title="'+esc(t('task.important'))+'">'+icons.flag+'</span>':'')
    +'<span class="sr-only">'+(sel?esc(t('card.sr_open'))+' ':'')+(x.important?esc(t('card.sr_important'))+' ':'')+t('card.sr_progress',{p:'<span class="sr-progress">'+x.progress+'</span>'})+(read?'':(sel?' '+esc(t('card.sr_arrows')):'')+' '+esc(t('card.sr_alt')))+'</span></button>';
}
function drawList(){
  const list=$('#task-list');if(!list)return;
  const ts=projectTasks();let done=false;
  $('#task-count').textContent=ts.length;
  list.innerHTML=ts.length?ts.map((x,i)=>{const label=x.progress===100&&!done?'<div class="group-label">'+t('list.done')+'</div>':'';if(x.progress===100)done=true;return label+cardHTML(x,i)}).join('')
    :ghostCards(3)+'<div class="empty-list"><strong>'+t('list.empty')+'</strong><span>'+(readOnly()?t('list.empty_past'):t('list.empty_hint'))+'</span></div>';
  drawLegend();
}
function drawLegend(){
  const el=$('#legend');if(!el)return;
  const x=current();
  el.innerHTML='<div class="legend-bar">'+(x?'<i id="legend-marker" style="left:'+x.progress+'%"></i>':'')+'</div><div class="legend-text">'
    +(readOnly()?'<span>0%</span><span>50%</span><span>100%</span>'
      :'<span>↕ '+(coarse()?t('legend.hold_drag'):t('legend.drag'))+'</span><span class="'+(x?'':'dim')+'" title="'+esc(t('legend.sideways'))+'">↔ '+t('legend.progress')+'</span>')+'</div>';
}

/* ---------- Overview ---------- */
/* Summary: each series once (007). In the current week, the next one not finished; otherwise the week's first. */
function onePerSeries(occs){
  const at=localNow(),series=new Map(),out=[];
  for(const o of occs){if(o.repeat==='none'){out.push(o);continue}if(!series.has(o.id))series.set(o.id,[]);series.get(o.id).push(o)}
  for(const os of series.values())out.push(week===S.week?os.find(o=>o.end>at)||os[os.length-1]:os[0]);
  return out;
}
/* Empty: generic lines in place of content; the text stays for screen readers. */
const ghost=(n,text,kind='')=>'<p class="sr-only">'+esc(text)+'</p><div class="ghost'+(kind?' ghost-'+kind:'')+'" aria-hidden="true">'+'<div class="ghost-row"><b></b><span><i></i><i class="short"></i></span></div>'.repeat(n)+'</div>';
const ghostCards=n=>'<div class="ghost" aria-hidden="true">'+'<div class="ghost-card"><i class="tiny"></i><i></i><i class="short"></i></div>'.repeat(n)+'</div>';
function dashboardHTML(){
  const read=readOnly(),active=projectTasks().filter(x=>x.progress<100);
  const subs=active.flatMap(x=>openSubs(x).map(s=>({x,s})));
  const ref=read?Date.parse(addDays(week,7)+'T00:00:00'):Date.now()+offset;
  const age=x=>Math.max(0,Math.floor((ref-Date.parse(x.lastActivity))/DAY));
  const stale=week>S.week?[]:active.filter(x=>age(x)>=3);
  const flag='<span class="mini-flag" title="'+esc(t('task.important'))+'">'+icons.flag+'</span>';
  /* Agenda: due dates of open tasks (every project) before the same day's events; overdue on top. */
  const we=addDays(week,7),open=S.dues.filter(x=>x.progress<100);
  const items=[
    ...(week===S.week?open.filter(x=>x.due<week).map(x=>({key:'0'+x.due,x,late:true})):[]),
    ...open.filter(x=>x.due>=week&&x.due<we).map(x=>({key:x.due+' ',x})),
    ...onePerSeries(events()).map(e=>({key:e.start,e}))
  ].sort((a,b)=>a.key.localeCompare(b.key));
  const row=r=>{
    if(r.e){const e=r.e;return '<button type="button" class="event-row" data-act="event" data-id="'+esc(e.id)+'" data-occ="'+e.start+'"><span class="event-day"><strong>'+e.start.slice(8,10)+'</strong><small>'+esc(weekday(e.start))+'</small></span><span class="row-text"><strong>'+esc(e.title)+'</strong><small>'+esc(e.projectId?pname(e.projectId):t('project.none'))+(e.repeat!=='none'?' · '+esc(repeatText(e)):'')+'</small></span><span class="event-time">'+(e.allDay?t('event.all_day'):e.start.slice(11,16))+'</span></button>'}
    const x=r.x,late=r.late||dueState(x)==='overdue';
    return '<button type="button" class="event-row due-row'+(late?' overdue':'')+'" data-act="open-task" data-id="'+esc(x.id)+'"><span class="event-day due"><strong>'+x.due.slice(8,10)+'</strong><small>'+esc(r.late?monthShort(x.due):weekday(x.due))+'</small></span><span class="row-text"><strong>'+esc(titleOf(x))+'</strong><small>'+(x.important?flag:'')+esc((late?t('agenda.overdue_prefix'):t('agenda.due_prefix'))+pname(x.projectId))+'</small></span><span class="event-time due-tag">'+(late?t('agenda.overdue_tag'):t('agenda.due_tag'))+'</span></button>';
  };
  const agenda=S.agendaWeek===week
    ?(items.length?'<div class="agenda-list">'+items.slice(0,9).map(row).join('')+'</div>':ghost(2,t('agenda.empty'),'agenda'))+(items.length>9?'<p class="hint">'+esc(t('agenda.more',{n:items.length-9}))+'</p>':'')
    :'<p class="empty">'+t('agenda.offline')+'</p>';
  const nhtml=S.notes[week+'|'+project]||'';
  return '<div class="dashboard"><div class="dashboard-grid">'
    +'<section class="panel p-notes week-notes" aria-label="'+esc(t('notes.week'))+'"><div class="panel-head notes-head"><h2>'+t('notes.week')+'</h2>'+(read?'':'<div class="fmt-bar notes-bar">'+toolsHTML()+'<div id="link-slot"></div></div>')+'</div>'
    +conflictHTML('week.notes|'+project+'|'+week)
    +'<div id="notes" class="notes"'+(read?' aria-readonly="true"':' contenteditable="true"')+' role="textbox" aria-multiline="true" aria-label="'+esc(t('notes.week'))+'" spellcheck="true" data-placeholder="'+esc(read?t('notes.week_empty'):t('notes.week_placeholder'))+'">'+(read?sanitizeHTML(nhtml):toEditor(nhtml))+'</div>'
    +(read?'':'<div id="link-bubble" class="link-bubble" role="toolbar" aria-label="'+esc(t('link.label'))+'" hidden></div>')+'</section>'
    +'<section class="panel p-subs"><div class="panel-head"><h2>'+t('dash.open_subtasks')+'</h2><span>'+subs.length+'</span></div>'
    +(subs.length?subs.map(({x,s})=>'<div class="dash-row"><button type="button" class="check" data-act="dash-done" data-task="'+esc(x.id)+'" data-id="'+esc(s.id)+'" aria-label="'+esc(t('subtask.complete',{text:s.text}))+'"'+(read?' disabled':'')+'>'+icons.check+'</button><button type="button" class="row-link" data-act="task" data-id="'+esc(x.id)+'"><span class="row-text"><strong>'+esc(s.text)+'</strong><small>'+(x.important?flag:'')+esc(titleOf(x))+'</small></span></button></div>').join(''):ghost(3,t('dash.no_subtasks')))
    +'</section><section class="panel p-agenda"><div class="panel-head"><h2>'+t('dash.agenda')+'</h2>'+btn('calendar',t('dash.view_week'),'','quiet')+'</div>'+agenda
    +'</section><section class="panel p-stale"><div class="panel-head"><h2>'+t('dash.stale')+'</h2><span>'+t('dash.stale_hint')+'</span></div>'
    +(stale.length?stale.map(x=>'<button type="button" class="stale-row" data-act="task" data-id="'+esc(x.id)+'"><span class="stale-symbol" aria-hidden="true">↻</span><span class="row-text"><strong>'+esc(titleOf(x))+'</strong><small>'+(x.important?flag:'')+esc(t('dash.stale_days',{n:age(x)}))+'</small></span></button>').join(''):ghost(2,t('dash.stale_empty'),'stale'))
    +'</section></div></div>';
}

/* ---------- Task as a document ---------- */
const tool=(cmd,label,name,key)=>'<button type="button" class="tool" data-fmt="'+cmd+'" aria-label="'+esc(name)+'" title="'+esc(name)+' · '+key+'" aria-pressed="false">'+label+'</button>';
const toolsHTML=()=>'<div class="tools" role="toolbar" aria-label="'+esc(t('fmt.toolbar'))+'">'+tool('bold','<b>B</b>',t('fmt.bold'),'Ctrl+B')+tool('italic','<i>I</i>',t('fmt.italic'),'Ctrl+I')
  +'<details class="size-menu" id="size-menu"><summary class="tool" aria-label="'+esc(t('fmt.size'))+'" title="'+esc(t('fmt.size'))+'"><span id="size-label">'+sizeLabel('p')+'</span>'+icons.chevron+'</summary><div class="size-pop" role="menu">'+sizeOpt('h2','Ctrl+Alt+1')+sizeOpt('h3','Ctrl+Alt+2')+sizeOpt('p','Ctrl+Alt+0')+'</div></details>'
  +'<span class="tool-sep" aria-hidden="true"></span>'+tool('mark',icons.mark,t('fmt.mark'),'Ctrl+Shift+H')+tool('list',icons.list,t('fmt.list'),'Ctrl+Shift+8')+tool('link',icons.link,t('link.label'),'Ctrl+K')+'</div>';
const sizeOpt=(v,key)=>'<button type="button" data-fmt="block" data-value="'+v+'" class="opt-'+v+'" role="menuitemradio" aria-checked="false"><span>'+sizeLabel(v)+'</span><small>'+key+'</small></button>';
const deleteSlotHTML=x=>confirmTask
  ?'<span class="confirm-inline" role="group" aria-label="'+esc(t('task.confirm_delete'))+'"><span>'+t('task.delete_q')+'</span>'+btn('delete-task',t('common.delete'),x.id,'danger')+btn('cancel-delete-task',t('common.cancel'),'','ghost')+'</span>'
  :btn('ask-delete-task',icons.trash,x.id,'tool trash',t('task.delete'));
function subtasksHTML(x,read){
  const items=openSubs(x).map(s=>'<li class="subtask"><button type="button" class="check" data-act="sub-done" data-id="'+esc(s.id)+'" aria-label="'+esc(t('subtask.complete',{text:s.text}))+'"'+(read?' disabled':'')+'>'+icons.check+'</button><textarea class="sub-text" data-sub="'+esc(s.id)+'" rows="1" maxlength="300" aria-label="'+esc(t('subtask.label'))+'" spellcheck="true"'+(read?' readonly':'')+'>'+esc(s.text)+'</textarea>'+(read?'':btn('sub-del',icons.x,s.id,'sub-del',t('subtask.delete')))+'</li>').join('');
  return x.subtasks.map(s=>conflictHTML('subtask.text|'+s.id)).join('')
    +(items?'<ul class="checklist">'+items+'</ul>':'')+(read?'':'<form id="sub-form" class="sub-new"><label class="check ghost" for="sub-new-input" aria-hidden="true">'+icons.plus+'</label><input id="sub-new-input" name="text" placeholder="'+esc(t('subtask.new'))+'" maxlength="300" aria-label="'+esc(t('subtask.new'))+'" autocomplete="off" enterkeyhint="done"></form>');
}
function historyHTML(x,read){
  const items=[...x.subtasks.filter(s=>s.done).map(s=>({at:s.doneAt,s})),...x.log.map(l=>({at:l.at,l}))].sort((a,b)=>Date.parse(b.at)-Date.parse(a.at));
  if(!items.length)return '';
  return '<h2 class="doc-label">'+t('task.history')+'</h2><ul class="timeline">'+items.map(({s,l,at})=>s
    ?'<li class="hist"><button type="button" class="check checked" data-act="sub-reopen" data-id="'+esc(s.id)+'" aria-label="'+esc(t('subtask.reopen',{text:s.text}))+'" title="'+esc(t('subtask.reopen_title'))+'"'+(read?' disabled':'')+'>'+icons.check+'</button><span class="hist-text">'+esc(s.text)+'</span><time datetime="'+esc(at)+'">'+esc(stamp(at))+'</time>'+(read?'':btn('sub-del',icons.x,s.id,'sub-del',t('subtask.delete')))+'</li>'
    :'<li class="hist"><span class="hist-icon" aria-hidden="true">'+(l.kind==='system'?'↪':'•')+'</span><span class="hist-text">'+esc(l.text)+'</span><time datetime="'+esc(at)+'">'+esc(l.kind==='system'?fmt(at.slice(0,10)):stamp(at))+'</time></li>').join('')+'</ul>';
}
function metaHTML(x,read){
  const st=dueState(x);
  let due='';
  if(!read){
    const label=!x.due?t('due.label'):st==='overdue'?t('due.was',{day:fmtDay(x.due)}):st==='today'?t('due.today'):t('due.on',{day:fmtDay(x.due)});
    due='<span class="meta-sep">·</span><span class="due-ctl"><button type="button" class="due-chip'+(x.due?' set':'')+(st==='overdue'?' overdue':'')+'" data-act="due-pick" aria-label="'+esc(x.due?t('due.change_now',{day:fmtDay(x.due)}):t('due.set'))+'" title="'+esc(x.due?t('due.change'):t('due.set'))+'">'+icons.due+'<span>'+esc(label)+'</span></button>'
      +'<input type="date" id="due-input" class="due-input" value="'+esc(x.due)+'" tabindex="-1" aria-label="'+esc(t('due.label'))+'">'
      +(x.due?btn('due-clear',icons.x,'','due-clear',t('due.remove')):'')+'</span>';
  }else if(x.due)due='<span class="meta-sep">·</span><span class="due-chip set">'+icons.due+'<span>'+esc(t('due.on',{day:fmtDay(x.due)}))+'</span></span>';
  return '<p class="doc-meta" id="doc-meta"><span class="meta-dot" aria-hidden="true"></span><span>'+esc(pname(x.projectId))+'</span><span class="meta-sep">·</span><span>'+esc(t('task.week_of',{date:fmt(x.week)}))+'</span>'+(x.carries?'<span class="meta-sep">·</span><span>'+esc(t('task.carried',{n:x.carries+1}))+'</span>':'')+due+'</p>';
}
function refreshMeta(x){const m=$('#doc-meta');if(m)m.outerHTML=metaHTML(x,readOnly())}
function setDue(x,v){
  v=validDate(v)?v:'';if(v===x.due)return;
  x.due=v;touch(x);persistTask(x);data.enqueue({op:'task.due',id:x.id,value:v||null});syncDue(x);refreshMeta(x);drawList();
}
function gotoTask(id){
  const x=liveTask(id);if(!x)return;
  show(null);project=x.projectId;week=x.week;addingProject=false;pane={id};render();
  cardFor(id)?.scrollIntoView({block:'nearest'});
}
function docHTML(x){
  const read=readOnly();
  const bar=read?'<div class="doc-bar read-bar"><span>'+t('task.snapshot')+'</span></div>'
    :'<div class="doc-bar fmt-bar">'+toolsHTML()
      +'<div class="doc-actions">'+btn('flag',icons.flag,x.id,'tool flag',x.important?t('task.unmark_important'):t('task.mark_important'),'aria-pressed="'+x.important+'"')+'<span id="delete-slot">'+deleteSlotHTML(x)+'</span></div><div id="link-slot"></div></div>';
  return '<article class="doc pc'+(read?' is-read':'')+'" style="--p:'+x.progress+'">'+bar
    +'<div class="doc-page">'+conflictHTML('task.title|'+x.id)+'<textarea id="doc-title" class="doc-title" rows="1" maxlength="160" placeholder="'+esc(t('task.untitled'))+'" aria-label="'+esc(t('task.title'))+'"'+(read?' readonly':'')+'>'+esc(x.title)+'</textarea>'
    +metaHTML(x,read)
    +'<section class="subtasks" id="subtasks" aria-label="'+esc(t('task.subtasks'))+'">'+subtasksHTML(x,read)+'</section>'
    +conflictHTML('task.notes|'+x.id)
    +'<div id="notes" class="notes"'+(read?' aria-readonly="true"':' contenteditable="true"')+' role="textbox" aria-multiline="true" aria-label="'+esc(t('task.notes'))+'" spellcheck="true" data-placeholder="'+esc(read?t('task.notes_empty'):t('task.notes_placeholder'))+'">'+(read?sanitizeHTML(x.description):toEditor(x.description))+'</div>'
    +'<section class="history" id="history" aria-label="'+esc(t('task.history'))+'">'+historyHTML(x,read)+'</section></div>'
    +(read?'':'<div id="link-bubble" class="link-bubble" role="toolbar" aria-label="'+esc(t('link.label'))+'" hidden></div>')+'</article>';
}
function drawDetail(){
  const root=$('#detail');if(!root)return;
  detachEditor();
  const x=current();
  if(pane&&!x)pane=null;
  if(!x){
    root.className='';root.innerHTML=dashboardHTML();
    const n=$('#notes');if(n){ed={kind:'week',key:week+'|'+project,week,projectId:project,taskId:null,read:readOnly(),notes:n,title:null,notesDirty:false,titleDirty:false,edited:false};notesEmpty()}
    return;
  }
  root.className='doc-view';root.innerHTML=docHTML(x);root.scrollTop=0;
  ed={kind:'task',taskId:x.id,read:readOnly(),notes:$('#notes'),title:$('#doc-title'),notesDirty:false,titleDirty:false,edited:false};
  autosize(ed.title);sizeSubs();notesEmpty();updateToolbar();
}
function refreshSubs(x){
  const input=$('#sub-new-input'),draftText=input?input.value:'',hadFocus=document.activeElement===input;
  const a=$('#subtasks'),h=$('#history');
  if(a)a.innerHTML=subtasksHTML(x,readOnly());
  if(h)h.innerHTML=historyHTML(x,readOnly());
  sizeSubs();
  const n=$('#sub-new-input');if(n){n.value=draftText;if(hadFocus)n.focus()}
  drawList();
}
function afterSubChange(x){if(pane?.id===x.id&&$('#subtasks'))refreshSubs(x);else{if(!pane)drawDetail();drawList()}}

/* ---------- Editing: title and notes ---------- */
const autosize=el=>{if(!el)return;el.style.height='auto';el.style.height=el.scrollHeight+'px'};
const sizeSubs=()=>document.querySelectorAll('.sub-text').forEach(autosize);
function notesEmpty(){if(!ed)return;const n=ed.notes;n.classList.toggle('is-empty',!n.textContent.trim()&&!n.querySelector('li,h2,h3,img'))}
/* The footer says there is unsaved text from the first keystroke. */
const typing=()=>{if(data.state().kind==='saved')setStorage(t('storage.saving'))};
function markNotesDirty(){if(!ed||ed.read)return;ed.notesDirty=true;typing();ed.edited=true;clearTimeout(notesTimer);notesTimer=setTimeout(saveNotes,400);notesEmpty()}
const storedNotes=()=>ed.kind==='week'?(S.notes[ed.key]||''):(liveTask(ed.taskId)?.description??'');
function saveNotes(){
  clearTimeout(notesTimer);
  if(!ed||ed.read||!ed.notesDirty)return;
  ed.notesDirty=false;
  const html=sanitizeHTML(ed.notes.innerHTML);
  if(ed.kind==='week'){
    if(ed.week<S.week)return;
    if(html!==(S.notes[ed.key]||'')){
      S.notes[ed.key]=html;persist(ed.week,ed.projectId);
      data.enqueue({op:'week.notes',project_id:ed.projectId,week:ed.week,value:html,base_rev:S.notesRev[ed.key]||0});
    }
    return;
  }
  const x=liveTask(ed.taskId);if(!x||x.week<S.week)return;
  if(html!==x.description){x.description=html;touch(x);persistTask(x);data.enqueue({op:'task.notes',id:x.id,value:html,base_rev:x.rev.notes})}
}
function saveTitle(){
  clearTimeout(titleTimer);
  if(!ed||ed.read||!ed.titleDirty)return;
  ed.titleDirty=false;
  const x=liveTask(ed.taskId);if(!x||x.week<S.week)return;
  const v=ed.title.value.replace(/[\r\n]+/g,' ').slice(0,160);
  if(v!==x.title){x.title=v;touch(x);persistTask(x);data.enqueue({op:'task.title',id:x.id,value:v,base_rev:x.rev.title});if(x.due)syncDue(x)}
}
function liveTitle(v){
  if(!ed||!ed.taskId)return;const c=cardFor(ed.taskId)?.querySelector('.card-title');if(!c)return;
  const s=v.trim();c.textContent=s||t('task.untitled');c.classList.toggle('untitled',!s);
}
function flushEdits(){if(ed&&!ed.read){saveNotes();saveTitle()}}
function detachEditor(){flushEdits();ed=null;lastRange=null;linkCtx=null;bubbleLink=null}

/* Selection and formatting commands */
function selectionInNotes(){const s=getSelection();return !!(ed&&s.rangeCount&&ed.notes.contains(s.getRangeAt(0).commonAncestorContainer))}
function caretFromPoint(x,y){
  if(document.caretPositionFromPoint){const p=document.caretPositionFromPoint(x,y);if(p){const r=document.createRange();r.setStart(p.offsetNode,p.offset);r.collapse(true);return r}}
  return document.caretRangeFromPoint?document.caretRangeFromPoint(x,y):null;
}
function placeCaret(atEnd){
  if(!ed||ed.read)return;
  const n=ed.notes,node=atEnd?n.lastChild:n.firstChild,r=document.createRange();
  n.focus({preventScroll:!atEnd});
  if(node&&node.nodeType===1&&!node.textContent){r.setStart(node,0);r.collapse(true)}
  else{r.selectNodeContents(node&&node.nodeType===1?node:n);r.collapse(!atEnd)}
  const s=getSelection();s.removeAllRanges();s.addRange(r);lastRange=r.cloneRange();
}
function setCaret(range){const s=getSelection();s.removeAllRanges();s.addRange(range);lastRange=range.cloneRange()}
function restoreSelection(){
  if(document.activeElement!==ed.notes)ed.notes.focus({preventScroll:true});
  if(selectionInNotes())return;
  if(lastRange&&ed.notes.contains(lastRange.commonAncestorContainer))setCaret(lastRange);else placeCaret(true);
}
function isHighlighted(){
  const s=getSelection();if(!s.rangeCount)return false;
  for(let n=s.anchorNode;n&&n!==ed.notes;n=n.parentNode){
    if(n.nodeType!==1)continue;
    if(n.tagName==='MARK')return true;
    const bg=n.style&&n.style.backgroundColor;if(bg)return !clearColor(bg);
  }
  return false;
}
function currentBlock(){
  for(let n=getSelection().anchorNode;n&&n!==ed.notes;n=n.parentNode){if(n.nodeType!==1)continue;const tag=n.tagName;if(tag==='H2'||tag==='H3')return tag.toLowerCase();if(tag==='P'||tag==='LI'||tag==='DIV')return 'p'}
  return 'p';
}
function setPressed(f,on){const b=document.querySelector('.fmt-bar [data-fmt="'+f+'"]');if(b)b.setAttribute('aria-pressed',on?'true':'false')}
function updateToolbar(){
  if(!ed||ed.read)return;
  const inside=selectionInNotes(),q=k=>{try{return inside&&document.queryCommandState(k)}catch(_){return false}};
  setPressed('bold',q('bold'));setPressed('italic',q('italic'));setPressed('list',q('insertUnorderedList'));setPressed('mark',inside&&isHighlighted());
  setPressed('link',!!linkCtx||(inside&&!!linkAt()));
  const block=inside?currentBlock():'p',label=$('#size-label');
  if(label)label.textContent=sizeLabel(block);
  document.querySelectorAll('.size-pop [data-value]').forEach(b=>b.setAttribute('aria-checked',String(b.dataset.value===block)));
}
function format(kind,value){
  if(!ed||ed.read)return;
  if(kind==='link'){if(linkCtx)closeLinkForm(true);else openLinkForm();return}
  restoreSelection();
  try{
    if(kind==='bold'||kind==='italic')document.execCommand(kind,false,null);
    else if(kind==='list')document.execCommand('insertUnorderedList',false,null);
    else if(kind==='block')document.execCommand('formatBlock',false,value);
    else if(kind==='mark'){const on=isHighlighted();document.execCommand('styleWithCSS',false,true);document.execCommand('hiliteColor',false,on?'transparent':HL);document.execCommand('styleWithCSS',false,false)}
  }catch(_){}
  markNotesDirty();updateToolbar();
}
function insertPlain(text){if(/[\r\n]/.test(text))document.execCommand('insertHTML',false,textToHtml(text)||'<p><br></p>');else document.execCommand('insertText',false,text)}

/* ---------- Links in notes ---------- */
function linkAt(){
  const s=getSelection();if(!ed||!s.rangeCount)return null;
  for(const start of [s.anchorNode,s.focusNode])for(let n=start;n&&n!==ed.notes;n=n.parentNode)if(n.nodeType===1&&n.tagName==='A')return n;
  return null;
}
function openLinkForm(anchor){
  if(!ed||ed.read)return;
  restoreSelection();
  const s=getSelection(),range=s.rangeCount?s.getRangeAt(0).cloneRange():null;
  anchor=anchor||linkAt();
  const selected=range&&!range.collapsed?range.toString():'',href=anchor?anchor.getAttribute('href')||'':'';
  const prefill=anchor?(isFileLink(href)?nativePath(href):href):(selected&&autoLink(selected)?selected.trim():'');
  linkCtx={anchor,range};hideBubble();
  const slot=$('#link-slot');if(!slot)return;
  slot.innerHTML='<form id="link-form" class="link-pop" aria-label="'+esc(anchor?t('link.edit'):t('link.insert_title'))+'"><label>'+t('link.address')+'<input name="href" value="'+esc(prefill)+'" placeholder="'+esc(t('link.address_placeholder'))+'" autocomplete="off" spellcheck="false"></label>'
    +'<label>'+t('link.text')+'<input name="text" value="'+esc(anchor?anchor.textContent:selected)+'" placeholder="'+esc(t('link.optional'))+'" autocomplete="off"></label><p class="hint">'+esc(t('link.file_hint'))+'</p>'
    +'<div class="link-actions"><button class="primary">'+(anchor?t('common.save'):t('link.insert'))+'</button>'+btn('link-cancel',t('common.cancel'),'','ghost')+(anchor?btn('link-unlink',t('link.remove'),'','ghost push'):'')+'</div><p class="error" role="alert"></p></form>';
  slot.querySelector('input[name="href"]').focus();
  setPressed('link',true);
}
function closeLinkForm(refocus){
  const ctx=linkCtx;linkCtx=null;
  const slot=$('#link-slot');if(slot)slot.innerHTML='';
  if(!ed)return;
  setPressed('link',false);
  if(refocus&&ctx?.range&&ed.notes.contains(ctx.range.commonAncestorContainer)){ed.notes.focus({preventScroll:true});setCaret(ctx.range)}
}
function caretAfter(node){const r=document.createRange();r.setStartAfter(node);r.collapse(true);setCaret(r)}
function applyLink(form){
  const err=m=>{form.querySelector('.error').textContent=m};
  const res=parseLink(form.elements.href.value);if(res.error){err(res.error);return}
  const ctx=linkCtx;if(!ctx||!ed)return;
  const href=res.href,typed=form.elements.text.value.replace(/\s+/g,' ').trim();
  closeLinkForm(true);
  const a=ctx.anchor;
  if(a&&ed.notes.contains(a)){
    a.setAttribute('href',href);
    if(typed&&typed!==a.textContent)a.textContent=typed;
    caretAfter(a);
  }else{
    const selected=ctx.range&&!ctx.range.collapsed?ctx.range.toString().replace(/\s+/g,' ').trim():'';
    if(selected&&(!typed||typed===selected))document.execCommand('createLink',false,href);
    else document.execCommand('insertHTML',false,'<a href="'+esc(href)+'">'+esc(typed||(isFileLink(href)?fileName(href):linkLabel(href)))+'</a>');
    const s=getSelection();if(s.rangeCount){const r=s.getRangeAt(0).cloneRange();r.collapse(false);setCaret(r)}
  }
  markNotesDirty();updateToolbar();
}
function unlink(a){
  if(!a||!ed||!ed.notes.contains(a))return;
  ed.notes.focus({preventScroll:true});
  const r=document.createRange();r.selectNodeContents(a);setCaret(r);
  document.execCommand('unlink',false,null);
  const s=getSelection();if(s.rangeCount){const c=s.getRangeAt(0).cloneRange();c.collapse(false);setCaret(c)}
  hideBubble();markNotesDirty();updateToolbar();
}
function updateBubble(){
  const b=$('#link-bubble');if(!b||!ed||ed.read)return;
  const a=!linkCtx&&document.activeElement===ed.notes&&selectionInNotes()?linkAt():null;
  if(!a){hideBubble();return}
  bubbleLink=a;
  const href=a.getAttribute('href')||'',file=isFileLink(href),canOpen=!file||location.protocol==='file:';
  b.innerHTML='<span class="lb-url" title="'+esc(file?nativePath(href):href)+'">'+(file?icons.file:icons.link)+'<span>'+esc(linkLabel(href))+'</span></span>'
    +(canOpen?btn('link-open',t('link.open'),'','lb-main'):'')+(file?btn('link-copy',t('link.copy_path'),'',canOpen?'':'lb-main'):'')
    +btn('link-edit',icons.pencil,'','',t('link.edit'))+btn('link-remove',icons.unlink,'','',t('link.remove'));
  b.hidden=false;
  const doc=b.parentElement,dr=doc.getBoundingClientRect(),rects=a.getClientRects(),r=rects[rects.length-1]||a.getBoundingClientRect();
  b.style.top=(r.bottom-dr.top+6)+'px';
  b.style.left=Math.max(12,Math.min(r.left-dr.left,dr.width-b.offsetWidth-12))+'px';
}
function hideBubble(){const b=$('#link-bubble');if(b&&!b.hidden)b.hidden=true;bubbleLink=null}
function openLink(href){
  if(!href)return;
  if(isFileLink(href)&&location.protocol!=='file:'){copyPath(href,true);return}
  const a=document.createElement('a');a.href=href;if(!/^mailto:/i.test(href)){a.target='_blank';a.rel='noopener noreferrer'}
  document.body.append(a);a.click();a.remove();
}
async function copyText(s){
  try{await navigator.clipboard.writeText(s);return true}catch(_){
    const ta=document.createElement('textarea');ta.value=s;ta.setAttribute('readonly','');ta.style.cssText='position:fixed;opacity:0;top:0;left:0';document.body.append(ta);ta.select();
    let ok=false;try{ok=document.execCommand('copy')}catch(_){}ta.remove();return ok;
  }
}
async function copyPath(href,explain){
  const path=nativePath(href),ok=await copyText(path);
  toast(ok?(explain?t('link.copied_explain'):t('link.copied')):t('link.copy_failed',{path}));
}

/* ---------- Progress from the card ---------- */
function setProgress(x,v){
  v=Math.max(0,Math.min(100,Math.round(v)));if(v===x.progress)return;
  x.progress=v;const card=cardFor(x.id);
  if(card){card.style.setProperty('--p',v);const sr=card.querySelector('.sr-progress');if(sr)sr.textContent=v}
  const m=$('#legend-marker');if(m)m.style.left=v+'%';
  const doc=$('.doc');if(doc&&ed?.taskId===x.id)doc.style.setProperty('--p',v);
}
function commitProgress(x,start,keyboard){
  if(x.progress===start)return;
  touch(x);
  /* When done, the task goes to the end of Done; when reopened, to the end of the open ones. */
  if((start===100)!==(x.progress===100)){x.order=lastOrder(x.week,x.projectId)+1;drawList();if(keyboard)cardFor(x.id)?.focus({preventScroll:true})}
  persistTask(x);data.enqueue({op:'task.progress',id:x.id,value:x.progress});if(x.due)syncDue(x);
  if(keyboard)srSay(t('sr.progress',{n:x.progress}));
}

/* ---------- Reordering by dragging ----------
   Mouse: drag the card vertically. Touch: hold for a moment and drag; swiping without holding scrolls the list.
   On the selected card, dragging sideways still adjusts progress. */
const HOLD_MS=350;
function beginSort(){
  const g=gesture,list=$('#task-list');if(!g||!list)return;
  const done=g.t.progress===100,r=g.card.getBoundingClientRect();
  g.mode='sort';g.list=list;g.offX=g.x0-r.left;g.offY=g.y0-r.top;
  g.grid=getComputedStyle(list).display==='grid';
  g.peers=[...list.querySelectorAll('.task-card')].filter(c=>c!==g.card&&(liveTask(c.dataset.id)?.progress===100)===done);
  g.card.classList.add('reordering');document.body.classList.add('is-sorting');
  try{g.card.setPointerCapture(g.pid)}catch(_){}
  if(g.touch&&navigator.vibrate)try{navigator.vibrate(10)}catch(_){}
  moveSort();
}
function moveSort(){
  const g=gesture;if(!g||g.mode!=='sort')return;
  const list=g.list,card=g.card,lr=list.getBoundingClientRect();
  const vx=g.x-g.offX-(lr.left+list.clientLeft)+list.scrollLeft,vy=g.y-g.offY-(lr.top+list.clientTop)+list.scrollTop;
  const cx=vx+card.offsetWidth/2,cy=vy+card.offsetHeight/2;
  let before=null;
  for(const s of g.peers){
    const sx=s.offsetLeft+s.offsetWidth/2,sy=s.offsetTop+s.offsetHeight/2,half=s.offsetHeight/2;
    if(g.grid?(sy>cy+half||(Math.abs(sy-cy)<=half&&sx>cx)):sy>cy){before=s;break}
  }
  const last=g.peers[g.peers.length-1];
  const inPlace=!last||(before?card.nextElementSibling===before:last.nextElementSibling===card);
  if(!inPlace){
    const prev=new Map(g.peers.map(s=>[s,[s.offsetLeft,s.offsetTop]]));
    if(before)list.insertBefore(card,before);else last.after(card);
    try{card.setPointerCapture(g.pid)}catch(_){}
    for(const s of g.peers){
      const [l,top]=prev.get(s),dx=l-s.offsetLeft,dy=top-s.offsetTop;
      if(dx||dy){s.style.transition='none';s.style.transform='translate('+dx+'px,'+dy+'px)';void s.offsetWidth;s.style.transition='transform .16s ease';s.style.transform=''}
    }
  }
  card.style.transform='translate('+(g.grid?vx-card.offsetLeft:0)+'px,'+(vy-card.offsetTop)+'px)';
}
function scrollSpeed(g){const r=g.list.getBoundingClientRect(),e=44;return g.y<r.top+e?-Math.ceil((r.top+e-g.y)/3):g.y>r.bottom-e?Math.ceil((g.y-r.bottom+e)/3):0}
function autoScroll(){
  if(scrollFrame||!gesture||gesture.mode!=='sort'||!scrollSpeed(gesture))return;
  const step=()=>{
    scrollFrame=0;const g=gesture;if(!g||g.mode!=='sort')return;
    const v=Math.max(-16,Math.min(16,scrollSpeed(g)));if(!v)return;
    const top=g.list.scrollTop;g.list.scrollTop+=v;if(g.list.scrollTop!==top)moveSort();
    scrollFrame=requestAnimationFrame(step);
  };
  scrollFrame=requestAnimationFrame(step);
}
/* Ids of one group (open or done) in the given order. */
const group=(ids,done)=>ids.filter(id=>(liveTask(id)?.progress===100)===done);
function finishSort(g){
  const card=g.card;
  card.style.transition='transform .15s ease';card.style.transform='';
  const done=g.t.progress===100,cards=[...g.list.querySelectorAll('.task-card')].map(c=>c.dataset.id),ids=group(cards,done);
  if(ids.join()!==group(projectTasks().map(x=>x.id),done).join()){
    cards.forEach((id,i)=>{const x=liveTask(id);if(x)x.order=i});
    persist();data.enqueue({op:'task.reorder',project_id:project,week,ids});srSay(t('sr.order_updated'));
  }
  setTimeout(()=>{if(!gesture)drawList()},170);
}
function moveByKeyboard(card,dir){
  const ts=projectTasks(),i=ts.findIndex(x=>x.id===card.dataset.id),x=ts[i],o=ts[i+dir];
  if(!x||!o||(o.progress===100)!==(x.progress===100))return;
  ts.forEach((y,k)=>{y.order=k});[x.order,o.order]=[o.order,x.order];
  persist();data.enqueue({op:'task.reorder',project_id:project,week,ids:group(projectTasks().map(y=>y.id),x.progress===100)});
  drawList();cardFor(x.id)?.focus();srSay(t('sr.position',{i:i+dir+1,n:ts.length}));
}

/* ---------- Actions ---------- */
function show(next){
  flushEdits();
  if(pane&&!readOnly()){const x=liveTask(pane.id);if(x&&isBlank(x)){S.tasks=S.tasks.filter(y=>y!==x);persistTask(x);data.enqueue({op:'task.delete',id:x.id})}}
  pane=next;confirmTask=false;
}
/* Closes the open task and goes back to the same week's overview, returning focus to the card. */
function closeTask(){
  const id=pane?.id;if(!id)return;
  show(null);drawList();drawDetail();
  cardFor(id)?.focus({preventScroll:true});
}
/* Switching week or project: reads from the server (or the cache, offline) before drawing. */
/* Last project and visibility choice, per device and per account (006 R4). */
const remember=(k,v)=>{try{localStorage.setItem('semana-'+k+'|'+account.id,v)}catch(_){}};
const remembered=k=>{try{return localStorage.getItem('semana-'+k+'|'+account.id)}catch(_){return null}};
/* Only the latest navigation draws: an earlier one that finishes later does not bring its screen back (nor the agenda). */
let navigation=0;
async function goTo(w,p=project){
  show(null);addingProject=false;
  const n=++navigation,valid=()=>n===navigation;
  try{await load(p,w);await loadAgenda(w,valid)}
  catch(e){
    if(!valid())return false;
    if(e.kind==='session'){loginScreen(e);return false}
    toast(e.kind==='offline'?t('week.offline'):t('week.failed'));
    if(S){drawToolbar();drawList();drawDetail()}
    return false;
  }
  if(!S||!valid())return false;
  week=w;project=p;remember('project',p);render();return true;
}
async function newTask(){
  const w=week<S.week?S.week:week;
  show(null);
  if(w!==week&&!await goTo(w))return;
  const x={id:crypto.randomUUID(),projectId:project,week:w,title:'',description:'',important:false,order:lastOrder(w,project)+1,progress:0,createdAt:now(),lastActivity:now(),carries:0,subtasks:[],log:[],rev:{title:0,notes:0}};
  S.tasks.push(x);pane={id:x.id};persistTask(x);data.enqueue({op:'task.create',id:x.id,project_id:project,week:w});
  drawList();drawDetail();
  cardFor(x.id)?.scrollIntoView({block:'nearest'});
  ed?.title.focus();
}
function setDone(x,id,done){
  const s=x.subtasks.find(y=>y.id===id);if(!s)return false;
  s.done=done;s.doneAt=done?now():'';touch(x);persistTask(x);data.enqueue({op:'subtask.done',id,done});return true;
}
function addSubtask(form){
  const x=editable();if(!x)return;
  const input=form.elements.text,text=input.value.replace(/\s+/g,' ').trim().slice(0,300);
  if(!text)return;
  const s={id:crypto.randomUUID(),text,done:false,createdAt:now(),doneAt:'',rev:0};
  x.subtasks.push(s);touch(x);persistTask(x);data.enqueue({op:'subtask.create',id:s.id,task_id:x.id,text});
  input.value='';refreshSubs(x);$('#sub-new-input')?.focus();
}
function deleteSub(x,id){
  const i=x.subtasks.findIndex(s=>s.id===id);if(i<0)return;
  const [s]=x.subtasks.splice(i,1);touch(x);persistTask(x);data.enqueue({op:'subtask.delete',id});refreshSubs(x);
  toast(t('subtask.deleted'),()=>{
    /* Undo recreates the subtask with the same id and the original dates; the text goes back to revision 0. */
    s.rev=0;x.subtasks.splice(Math.min(i,x.subtasks.length),0,s);touch(x);persistTask(x);
    data.enqueue({op:'subtask.create',id:s.id,task_id:x.id,text:s.text,created_at:s.createdAt,done_at:s.done?s.doneAt:null});
    afterSubChange(x);
  });
}
function toast(msg,undo,label=t('toast.undo')){
  const el=$('#toast');clearTimeout(toastTimer);toastUndo=undo||null;
  el.innerHTML='<span>'+esc(msg)+'</span>'+(undo?'<button type="button" data-act="undo">'+esc(label)+'</button>':'');
  el.classList.add('show');toastTimer=setTimeout(hideToast,msg.length>90?9000:6000);
}
function hideToast(){$('#toast').classList.remove('show');toastUndo=null}
function setConfirm(on){
  confirmTask=on;const slot=$('#delete-slot'),x=current();if(!slot||!x)return;
  slot.innerHTML=deleteSlotHTML(x);(on?slot.querySelector('.danger'):slot.querySelector('.trash'))?.focus();
}
function clickToNotes(e){
  const n=ed.notes,r=n.getBoundingClientRect();
  if(e.clientY<r.top)return;
  if(e.clientY>=r.bottom-2){placeCaret(true);return}
  const range=caretFromPoint(Math.min(Math.max(e.clientX,r.left+2),r.right-2),e.clientY);
  n.focus({preventScroll:true});
  if(range&&n.contains(range.startContainer))setCaret(range);else placeCaret(true);
}

/* ---------- Calendar (feature 002; prototype, lines 1581–1628) ---------- */
const events=()=>S.agendaWeek===week?S.events.flatMap(e=>occurrences(e,week)).sort((a,b)=>a.start.localeCompare(b.start)):[];
function openEvent(id,day,time,occ){
  const e=S.events.find(x=>x.id===id),date=day||(week===S.week?today():week),hour=time||'09:00';
  draft=e?{...clone(e),occurrence:occ?occ.slice(0,10):''}:{id:'',title:'',start:date+'T'+hour,end:date+'T'+String(Math.min(23,Number(hour.slice(0,2))+1)).padStart(2,'0')+':00',allDay:false,repeat:'none',until:'',projectId:filter||'',description:'',location:'',rev:0};
  if(draft.end<=draft.start)draft.end=addDays(date,1)+'T00:00';
  deleteEvent='';
  if(screen!=='calendar'){show(null);screen='calendar';render()}else drawCalendar();
  $('#event-form input[name="title"]')?.focus();
}
const FREQUENCIES=['none','daily','weekly','monthly'];
function eventEditor(){
  if(!draft)return '';
  const e=draft,a=e.allDay,series=e.id&&S.events.some(x=>x.id===e.id&&x.repeat!=='none');
  return '<aside class="event-editor"><div class="panel-head"><h2>'+(e.id?t('event.edit'):t('event.new'))+'</h2>'+btn('close-event',icons.x,'','icon-btn',t('event.close'))+'</div>'
    +(e.id?eventConflictHTML('event.save|'+e.id):'')
    +'<p class="hint">'+(series?t('event.series_hint'):t('event.hint'))+'</p>'
    +'<form id="event-form">'+field('title',t('event.title'),e.title,'text','required maxlength="160"')
    +'<label>'+t('event.description')+'<textarea name="description" rows="3" maxlength="10000">'+esc(e.description)+'</textarea></label>'
    +'<label class="check-label"><input name="allDay" type="checkbox"'+(a?' checked':'')+'> '+t('event.all_day')+'</label>'
    +'<label class="check-label" id="event-full"><input name="fullDay" type="checkbox"'+(a&&e.fullDay?' checked':'')+'> '+t('event.fill_day')+'</label>'
    +field('start',t('event.start'),a?e.start.slice(0,10):e.start,a?'date':'datetime-local','required data-prev="'+esc(a?e.start.slice(0,10):e.start)+'"')+field('end',a?t('event.last_day'):t('event.end'),a?addDays(e.end.slice(0,10),-1):e.end,a?'date':'datetime-local','required')
    +'<label>'+t('event.frequency')+'<select name="repeat">'+FREQUENCIES.map(v=>opt(v,t('freq.'+v),e.repeat)).join('')+'</select></label>'
    +'<div id="event-until"'+(e.repeat==='none'?' hidden':'')+'>'+field('until',t('event.until'),e.until,'date')+'</div>'
    +'<label>'+t('project.label')+'<select name="projectId">'+opt('',t('project.none'),e.projectId)+S.projects.map(p=>opt(p.id,p.name,e.projectId)).join('')+'</select></label>'
    +'<div class="field-link">'+field('location',t('event.location'),e.location,'text','maxlength="500"')+'<button type="button" class="icon-btn" data-act="open-location" aria-label="'+esc(t('event.open_link'))+'" title="'+esc(t('event.open_link'))+'"'+(parseLink(e.location).href?'':' hidden')+'>'+icons.external+'</button></div>'
    +'<button class="primary">'+t('event.save')+'</button><p class="error" role="alert"></p></form>'
    +(e.id?(deleteEvent===e.id?'<div class="confirm">'+(e.repeat!=='none'&&e.occurrence
        ?'<p>'+esc(t('event.delete_which',{day:fmtDay(e.occurrence)}))+'</p>'+btn('delete-occ',t('series.one'),e.id,'danger')+btn('delete-event',t('series.all'),e.id,'danger')
        :'<p>'+(e.repeat==='none'?t('event.delete_one_q'):t('event.delete_series_q'))+'</p>'+btn('delete-event',t('event.delete_yes'),e.id,'danger'))+btn('cancel-delete',t('common.cancel'))+'</div>'
      :btn('ask-delete-event',e.repeat==='none'?t('event.delete'):t('common.delete'),e.id,'danger')):'')+'</aside>';
}
function dueEventHTML(x){
  const st=dueState(x);
  return '<button type="button" class="due-event pc'+(st==='done'?' done':st==='overdue'?' overdue':'')+'" style="--p:'+x.progress+'" data-act="open-task" data-id="'+esc(x.id)+'" title="'+esc(t('cal.due_title',{title:titleOf(x),project:pname(x.projectId),state:st==='done'?t('cal.due_done'):st==='overdue'?t('cal.due_late'):''}))+'"><i class="dot" aria-hidden="true"></i><span>'+esc(titleOf(x))+'</span><i class="go" aria-hidden="true">'+icons.go+'</i></button>';
}
function drawCalendar(){
  const root=$('#calendar');if(!root)return;
  hideCard();
  if(S.agendaWeek!==week){root.innerHTML='<div class="calendar-heading"><h1>'+t('cal.heading')+'</h1></div><p class="empty">'+t('week.offline')+'</p>';return}
  const prev=$('.calendar-scroll')?.scrollTop;
  const dues=S.dues.filter(x=>x.due>=week&&x.due<addDays(week,7)&&(!filter||x.projectId===filter)).sort((a,b)=>(a.progress===100)-(b.progress===100)||(b.important-a.important)||titleOf(a).localeCompare(titleOf(b)));
  const ev=events().filter(e=>!filter||e.projectId===filter),days=Array.from({length:7},(_,i)=>addDays(week,i)),labels=t('cal.days').split(','),minute=s=>Number(s.slice(11,13))*60+Number(s.slice(14,16)),t0=today();
  const work=S.projects.find(p=>p.name==='Work'||p.name==='Trabalho')?.id;
  root.innerHTML='<div class="calendar-heading"><h1>'+t('cal.heading')+'</h1>'+btn('new-event',t('event.new_button'),'','primary')+'</div><div class="calendar-layout'+(draft?' with-editor':'')+'"><section class="calendar-frame"><div class="calendar-overflow">'
    +'<div class="day-head"><div></div>'+days.map((d,i)=>'<div class="'+(d===t0?'today':'')+'"><span>'+labels[i]+'</span><strong>'+d.slice(8)+'</strong></div>').join('')+'</div>'
    +(dues.length?'<div class="all-day due-strip" aria-label="'+esc(t('cal.due_strip'))+'"><small>'+t('cal.dues')+'</small>'+days.map(day=>'<div>'+dues.filter(x=>x.due===day).map(dueEventHTML).join('')+'</div>').join('')+'</div>':'')
    +(ev.some(e=>e.allDay&&!e.fullDay)?'<div class="all-day"><small>'+t('event.all_day')+'</small>'+days.map(day=>'<div>'+ev.filter(e=>e.allDay&&!e.fullDay&&e.start.slice(0,10)<=day&&e.end.slice(0,10)>day).map(e=>'<button type="button" class="all-day-event" data-act="event" data-id="'+esc(e.id)+'" data-occ="'+e.start+'" data-day="'+day+'"><span>'+esc(e.title)+'</span></button>').join('')+'</div>').join('')+'</div>':'')
    +'<div class="calendar-scroll"><div class="time-grid"><div class="time-labels">'+Array.from({length:24},(_,h)=>'<span style="top:'+h*60+'px">'+String(h).padStart(2,'0')+':00</span>').join('')+'</div>'
    +days.map(day=>{
      const list=ev.filter(e=>(!e.allDay||e.fullDay)&&e.start<addDays(day,1)+'T00:00'&&e.end>day+'T00:00').map(e=>{const a=e.start.slice(0,10)<day?0:minute(e.start),end=e.end.slice(0,10)>day?1440:minute(e.end);return {...e,a,b:Math.min(1440,Math.max(a+24,end))}});
      return '<div class="cal-day">'+Array.from({length:24},(_,h)=>'<button type="button" class="slot" data-act="slot" data-day="'+day+'" data-time="'+String(h).padStart(2,'0')+':00" style="top:'+h*60+'px" aria-label="'+esc(t('cal.slot',{date:fmt(day),h}))+'"></button>').join('')
        +layoutEvents(list).map(e=>'<button type="button" class="cal-event'+(work&&e.projectId===work?' work':'')+'" data-act="event" data-id="'+esc(e.id)+'" data-occ="'+e.start+'" data-day="'+day+'" data-top="'+e.a+'"'+(e.allDay?' data-full="1"':'')+' style="top:'+e.a+'px;height:'+(e.b-e.a)+'px;left:calc('+100*e.lane/e.columns+'% + 3px);width:calc('+100/e.columns+'% - 6px)"><small>'+(e.allDay?t('event.all_day'):e.start.slice(11,16))+(e.repeat!=='none'?' ↻':'')+'</small><strong>'+esc(e.title)+'</strong>'
          +(!e.allDay&&(e.end.slice(0,10)===day||e.end===addDays(day,1)+'T00:00')?'<span class="resize" aria-hidden="true"></span>':'')+'</button>').join('')+'</div>';
    }).join('')+'</div></div></div></section>'+eventEditor()+'</div>';
  const sc=$('.calendar-scroll');if(sc)sc.scrollTop=prev??7*60;
}
function eventValues(form){
  const d=new FormData(form),repeat=FREQUENCIES.includes(d.get('repeat'))?String(d.get('repeat')):'none',until=repeat==='none'?'':String(d.get('until')||'');
  return {...draft,title:String(d.get('title')||'').trim(),start:String(d.get('start')||'').slice(0,16),end:String(d.get('end')||'').slice(0,16),allDay:d.has('allDay'),fullDay:d.has('allDay')&&d.has('fullDay'),until,repeat,projectId:String(d.get('projectId')||''),location:String(d.get('location')||''),description:String(d.get('description')||'')};
}
function syncEventFrequency(el){
  if(el.name!=='repeat'||!el.closest('#event-form'))return;
  const box=$('#event-until');box.hidden=el.value==='none';if(box.hidden)box.querySelector('input').value='';
}
/* Start after end: the end follows, keeping the duration the event had (006 FR-002). */
function adjustEnd(start){
  const end=start.form.elements.end,day=start.type==='date',ms=v=>Date.parse(day?v+'T00:00Z':v+'Z');
  const before=start.dataset.prev||start.value,dur=Math.max(0,ms(end.value)-ms(before));
  start.dataset.prev=start.value;
  if(!Number.isFinite(dur)||!start.value||!end.value)return;
  if(day?end.value>=start.value:end.value>start.value)return;
  end.value=new Date(ms(start.value)+(day?dur:dur||3600000)).toISOString().slice(0,day?10:16);
}
/* Validates like the server (FR-022, FR-023) and queues the whole series. */
function saveEvent(form){
  const ev=eventValues(form),err=m=>{form.querySelector('.error').textContent=m};
  if(ev.allDay){if(!validDate(ev.start)||!validDate(ev.end))return err(t('event.bad_dates'));ev.start+='T00:00';ev.end=addDays(ev.end,1)+'T00:00'}
  const ok=s=>/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(s)&&validDate(s.slice(0,10));
  if(!ev.title||!ok(ev.start)||!ok(ev.end)||ev.end<=ev.start||Date.parse(ev.end+'Z')-Date.parse(ev.start+'Z')>31*DAY)return err(t('event.bad_range'));
  if(ev.until&&ev.until<ev.start.slice(0,10))return err(t('event.bad_until'));
  draft=null;submitEvent(ev);
}
function submitEvent(ev){
  delete ev.occurrence;
  if(!ev.id){ev.id=crypto.randomUUID();ev.rev=0}
  S.events=S.events.some(x=>x.id===ev.id)?S.events.map(x=>x.id===ev.id?ev:x):[...S.events,ev];
  data.enqueue({op:'event.save',...eventToAPI(ev),rev:undefined,base_rev:ev.rev||0});
  storeAgenda();drawCalendar();
}

/* ---------- Details card and dragging (006 R1, R2): mouse only ---------- */
const shift=(s,min)=>new Date(Date.parse(s+'Z')+min*60000).toISOString().slice(0,16);
function eventCardHTML(e,occ){
  const start=occ||e.start,end=shift(start,(Date.parse(e.end+'Z')-Date.parse(e.start+'Z'))/60000);
  const when=e.allDay?fmtDay(start.slice(0,10))+(dayDiff(start,end)>1?' – '+fmtDay(addDays(end.slice(0,10),-1)):'')+' · '+t('event.all_day')
    :fmtDay(start.slice(0,10))+' · '+start.slice(11,16)+'–'+end.slice(11,16);
  const desc=e.description.trim(),line=(label,v)=>v?'<p><span>'+label+'</span>'+esc(v)+'</p>':'';
  return '<strong>'+esc(e.title)+'</strong>'+line(t('card.when'),when)+line(t('card.repeats'),repeatText(e))+line(t('project.label'),e.projectId?pname(e.projectId):t('project.none'))+line(t('card.location'),e.location)
    +(desc?'<p class="ec-desc">'+esc(desc.length>160?desc.slice(0,160)+'…':desc)+'</p>':'');
}
let cardTimer=0;
function showCard(block){
  const e=S?.events.find(x=>x.id===block.dataset.id);if(!e)return;
  let card=$('#event-card');
  if(!card){document.body.insertAdjacentHTML('beforeend','<div id="event-card" class="event-card" role="tooltip"></div>');card=$('#event-card')}
  card.innerHTML=eventCardHTML(e,block.dataset.occ);card.hidden=false;
  block.setAttribute('aria-describedby','event-card');
  const r=block.getBoundingClientRect(),c=card.getBoundingClientRect(),m=8;
  let x=r.right+m;if(x+c.width>innerWidth-m)x=r.left-m-c.width;
  card.style.left=Math.max(m,x)+'px';card.style.top=Math.max(m,Math.min(r.top,innerHeight-c.height-m))+'px';
}
function hideCard(){clearTimeout(cardTimer);const c=$('#event-card');if(c)c.hidden=true;$('[aria-describedby="event-card"]')?.removeAttribute('aria-describedby')}
const BLOCK='.cal-event,.all-day-event';
document.addEventListener('pointerover',e=>{
  const b=e.target.closest?.(BLOCK);if(!b||e.pointerType!=='mouse'||drag||b.contains(e.relatedTarget))return;
  clearTimeout(cardTimer);cardTimer=setTimeout(()=>{if(b.isConnected&&!drag)showCard(b)},300);
});
document.addEventListener('pointerout',e=>{const b=e.target.closest?.(BLOCK);if(b&&!b.contains(e.relatedTarget)&&document.activeElement!==b)hideCard()});
document.addEventListener('focusin',e=>{if(e.target.matches?.(BLOCK))showCard(e.target)});
document.addEventListener('focusout',e=>{if(e.target.matches?.(BLOCK))hideCard()});

let drag=null,ignoreClick=false,seriesActions=null;
const hm=m=>String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0');
const minutesBetween=(a,b)=>(Date.parse(b+'Z')-Date.parse(a+'Z'))/60000;
document.addEventListener('pointerdown',e=>{
  const b=e.target.closest?.(BLOCK);if(!b||e.pointerType==='touch'||e.button!==0||!S||$('#series-pop'))return;
  const r=b.getBoundingClientRect();
  drag={b,x:e.clientX,y:e.clientY,dy:e.clientY-r.top,moving:false,edge:!!e.target.closest('.resize'),day:b.dataset.day,top:Number(b.dataset.top||0),newDay:b.dataset.day,newTop:Number(b.dataset.top||0),height:0};
});
document.addEventListener('pointermove',e=>{
  const a=drag;if(!a)return;
  if(!a.moving){if(Math.hypot(e.clientX-a.x,e.clientY-a.y)<4)return;a.moving=true;hideCard();a.b.classList.add('dragging');document.body.classList.add('is-dragging');a.b.setPointerCapture?.(e.pointerId)}
  if(a.edge){
    a.height=Math.min(1440-a.top,Math.max(15,Math.round((e.clientY-a.b.getBoundingClientRect().top)/15)*15));
    a.b.style.height=a.height+'px';return;
  }
  const band=a.b.classList.contains('all-day-event'),dayOnly=band||!!a.b.dataset.full;
  const target=document.elementsFromPoint(e.clientX,e.clientY).find(el=>band
    ?el.tagName==='DIV'&&el.parentElement?.matches('.all-day:not(.due-strip)')
    :el.classList?.contains('cal-day'));
  if(!target)return;
  const cols=[...target.parentElement.children].filter(el=>el.tagName==='DIV'&&!el.classList.contains('time-labels'));
  a.newDay=addDays(week,cols.indexOf(target));
  if(a.b.parentElement!==target)target.append(a.b);
  a.b.style.left='3px';a.b.style.width='calc(100% - 6px)';
  if(dayOnly)return;
  a.newTop=Math.max(0,Math.min(1440-15,Math.round((e.clientY-target.getBoundingClientRect().top-a.dy)/15)*15));
  a.b.style.top=a.newTop+'px';
  const label=a.b.querySelector('small');if(label&&!a.b.dataset.full)label.textContent=hm(a.newTop)+(label.textContent.includes('↻')?' ↻':'');
});
function drop(){
  const a=drag;drag=null;if(!a||!a.moving)return;
  /* the click the browser fires with this pointerup neither opens the editor nor closes the bubble */
  ignoreClick=true;setTimeout(()=>{ignoreClick=false});document.body.classList.remove('is-dragging');a.b.classList.remove('dragging');
  const e=S?.events.find(x=>x.id===a.b.dataset.id),occ=a.b.dataset.occ;
  if(!e){drawCalendar();return}
  let dStart=0,dEnd=0;
  if(a.edge){const endOcc=shift(occ,minutesBetween(e.start,e.end));dEnd=a.top+a.height-(dayDiff(a.day,endOcc)*1440+Number(endOcc.slice(11,13))*60+Number(endOcc.slice(14,16)))}
  else dStart=dEnd=dayDiff(a.day,a.newDay)*1440+(a.b.classList.contains('all-day-event')||a.b.dataset.full?0:a.newTop-a.top);
  if(!dStart&&!dEnd){drawCalendar();return}
  moveEvent(a.b,e,occ,dStart,dEnd);
}
/* Shifts start and end (in minutes); for a recurring one, asks whether it applies to this occurrence only (007). */
function moveEvent(block,e,occ,dStart,dEnd){
  const series=()=>{
    const ev=clone(e);ev.start=shift(e.start,dStart);ev.end=shift(e.end,dEnd);
    if(ev.until&&ev.until<ev.start.slice(0,10))ev.until=addDays(ev.until,dayDiff(e.start,ev.start));
    if(draft?.id===ev.id)draft=null;
    submitEvent(ev);
  };
  if(e.repeat==='none')return series();
  askSeries(block,t('series.ask'),()=>{
    if(draft?.id===e.id)draft=null;
    submitEvent({...clone(e),except:[...(e.except||[]),occ.slice(0,10)]});
    submitEvent({...clone(e),id:'',rev:0,repeat:'none',until:'',except:[],start:shift(occ,dStart),end:shift(shift(occ,minutesBetween(e.start,e.end)),dEnd)});
  },series);
}
function askSeries(block,text,one,series){
  closeSeries();
  document.body.insertAdjacentHTML('beforeend','<div id="series-pop" class="series-pop" role="dialog" aria-label="'+esc(text)+'"><p>'+esc(text)+'</p><div>'
    +btn('series-one',t('series.one'),'','primary')+btn('series-all',t('series.all'))+btn('series-cancel',t('common.cancel'),'','ghost')+'</div></div>');
  seriesActions={one,series};
  const pop=$('#series-pop'),r=block.getBoundingClientRect(),c=pop.getBoundingClientRect(),m=8;
  let x=r.right+m;if(x+c.width>innerWidth-m)x=r.left-m-c.width;
  pop.style.left=Math.max(m,x)+'px';pop.style.top=Math.max(m,Math.min(r.top,innerHeight-c.height-m))+'px';
  pop.querySelector('button').focus();
}
function closeSeries(redraw){if(!$('#series-pop'))return;$('#series-pop').remove();seriesActions=null;if(redraw)drawCalendar()}
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&$('#series-pop')){e.preventDefault();e.stopPropagation();closeSeries(true)}},true);
document.addEventListener('pointerup',drop);
document.addEventListener('pointercancel',()=>{if(drag?.moving){drag=null;document.body.classList.remove('is-dragging');drawCalendar()}else drag=null});
/* Due date or task: opens in its week and project (FR-031). */
async function openTask(id){
  const d=S.dues.find(x=>x.id===id)||liveTask(id);if(!d)return;
  draft=null;screen='tasks';
  if(!await goTo(d.week,d.projectId))return;
  pane={id};drawList();drawDetail();cardFor(id)?.scrollIntoView({block:'nearest'});
}

/* ---------- Search (feature 003; prototype, lines 1630–1727) ----------
   The account index comes from the server (or the cache, offline); what is in memory wins,
   including changes not sent yet (FR-016). The ranking is the prototype's, in pure.js. */
const fromIndex=x=>({id:x.id,projectId:x.project_id,week:x.week,title:x.title,description:x.notes,subtasks:x.subtasks.map(text=>({text})),progress:x.progress,important:x.important,due:x.due||'',lastActivity:x.updated_at});
function currentSearchItems(index){
  const local=new Map(S.tasks.map(x=>[x.id,x]));
  const all=[...(index?.tasks||[]).filter(x=>!local.has(x.id)).map(fromIndex),...local.values()];
  const notes={};
  for(const n of index?.notes||[])notes[n.week+'|'+n.project_id]=n.html;
  Object.assign(notes,S.notes);
  const evs=new Map((index?.events||[]).map(x=>[x.id,eventFromAPI(x)]));
  for(const e of S.events)evs.set(e.id,e);
  return searchItems(all,notes,[...evs.values()],today());
}
const weekLabel=w=>w===S.week?t('week.this'):w===addDays(S.week,-7)?t('week.last'):w===addDays(S.week,7)?t('week.next'):t('week.of',{date:fmt(w)});
function drawResults(){
  const {terms,list,recent}=search.res,ul=$('#search-results'),inp=$('#search-input');
  const offline=search.offline?'<li class="search-empty" role="presentation">'+t('search.offline')+'</li>':'';
  if(!list.length){ul.innerHTML=offline+'<li class="search-empty" role="presentation">'+(search.q.trim()?esc(t('search.nothing',{q:search.q.trim()})):t('search.no_open'))+'</li>';inp.removeAttribute('aria-activedescendant');return}
  ul.innerHTML=offline+(recent?'<li class="search-group" role="presentation">'+t('search.recent')+'</li>':'')+list.map((it,i)=>{
    const meta=[esc(pname(it.projectId)),esc(weekLabel(it.week))];
    if(it.kind==='task'){if(it.t.progress===100)meta.push(t('search.done'));else if(it.t.due)meta.push(esc(dueShort(it.t)))}
    if(it.kind==='event'){meta.length=0;meta.push(t('search.event'),esc(it.projectId?pname(it.projectId):t('project.none')),esc(fmtDay(it.day)+(it.e.allDay?'':' · '+it.e.start.slice(11,16))))}
    const lead=it.kind==='task'?'<i class="so-dot pc" style="--p:'+it.t.progress+'" aria-hidden="true"></i>':'<i class="so-icon" aria-hidden="true">'+(it.kind==='event'?icons.calendar:icons.notes)+'</i>';
    const flag=it.kind==='task'&&it.t.important?'<span class="mini-flag" title="'+esc(t('task.important'))+'">'+icons.flag+'</span>':'';
    const sn=snippetOf(it,terms);
    return '<li class="so" role="option" id="so-'+i+'" data-i="'+i+'" aria-selected="'+(i===search.sel)+'">'+lead+'<span class="so-body"><span class="so-title">'+markTerms(it.title,terms)+'</span><span class="so-meta">'+flag+meta.join(' · ')+'</span>'+(sn?'<span class="so-snippet">'+sn+'</span>':'')+'</span></li>';
  }).join('');
  inp.setAttribute('aria-activedescendant','so-'+search.sel);
  $('#so-'+search.sel)?.scrollIntoView({block:'nearest'});
}
const rank=()=>{search.res=rankSearch(search.items,search.q,S.week)};
function openSearch(){
  if(!S)return;
  if(search){closeSearch(true);return}
  flushEdits();
  search={q:'',sel:0,items:currentSearchItems(null),back:document.activeElement,offline:false};
  document.body.insertAdjacentHTML('beforeend','<div class="search-layer" id="search" role="dialog" aria-modal="true" aria-label="'+esc(t('search.label'))+'"><div class="search-box"><div class="search-field">'+icons.search
    +'<input id="search-input" type="text" role="combobox" aria-expanded="true" aria-controls="search-results" aria-autocomplete="list" aria-label="'+esc(t('search.placeholder'))+'" placeholder="'+esc(t('search.placeholder'))+'" autocomplete="off" spellcheck="false"><kbd>Esc</kbd></div>'
    +'<ul id="search-results" class="search-results" role="listbox" aria-label="'+esc(t('search.results'))+'"></ul><p class="search-foot"><span>'+t('search.foot_choose')+'</span><span>'+t('search.foot_open')+'</span><span>'+t('search.foot_close')+'</span></p></div></div>');
  rank();drawResults();
  $('#search-input').focus();
  const mine=search;
  data.search().then(index=>{
    if(search!==mine||!S)return;
    search.items=currentSearchItems(index);search.offline=!!index.offline;rank();drawResults();
  },e=>{if(e.kind==='session'){closeSearch(false);loginScreen(e)}});
}
function closeSearch(restore){
  const s=search;search=null;$('#search')?.remove();
  if(!restore||!s?.back||!document.contains(s.back))return;
  s.back.focus({preventScroll:true});
  if(ed&&s.back===ed.notes&&lastRange&&ed.notes.contains(lastRange.commonAncestorContainer))setCaret(lastRange);
}
async function chooseResult(i){
  const it=search?.res.list[i];if(!it)return;
  const terms=search.res.terms;closeSearch(false);
  if(it.kind==='event')return openEventResult(it);
  screen='tasks';draft=null;
  if(!await goTo(it.week,it.projectId))return;
  if(it.kind==='task'){pane={id:it.id};drawList();drawDetail();cardFor(it.id)?.scrollIntoView({block:'nearest'})}
  if(ed&&terms.length)revealIn(ed.notes,terms);
}
/* Event from search: calendar on the occurrence's week, with the block focused and the card open (006). */
async function openEventResult(it){
  show(null);screen='calendar';draft=null;
  if(filter&&it.projectId!==filter){filter='';remember('visibility','')}
  if(!await goTo(it.week))return;
  const blocks=[...document.querySelectorAll(BLOCK)].filter(x=>x.dataset.id===it.id),b=blocks.find(x=>x.dataset.day===it.day)||blocks[0];
  if(!b)return;
  b.scrollIntoView({block:'center'});b.focus({preventScroll:true});
}
/* Selects and shows the first occurrence of the terms inside a text. */
function revealIn(container,terms){
  const walker=document.createTreeWalker(container,NodeFilter.SHOW_TEXT);
  for(let n=walker.nextNode();n;n=walker.nextNode()){
    const f=fold(n.data);
    for(const term of terms){
      const i=f.indexOf(term);if(i<0)continue;
      if(container.isContentEditable)container.focus({preventScroll:true});
      const r=document.createRange();r.setStart(n,i);r.setEnd(n,i+term.length);
      const s=getSelection();s.removeAllRanges();s.addRange(r);if(container.isContentEditable)lastRange=r.cloneRange();
      n.parentElement.scrollIntoView({block:'center'});
      return true;
    }
  }
  return false;
}

/* ---------- Edit conflicts (FR-061) ----------
   A text changed on another device is never overwritten silently: the notice sits above the field
   and the discarded version stays copyable until the person closes the notice. */
const conflictKey=op=>op.op+'|'+(op.op==='week.notes'?op.project_id+'|'+op.week:op.id);
const isHTML=op=>op.op.endsWith('notes');
const whenText=v=>v.all_day?fmt(v.start)+(dayDiff(v.start,v.end)>1?t('conflict.to',{date:fmt(addDays(v.end.slice(0,10),-1))}):'')+' · '+t('conflict.all_day'):fmt(v.start)+' '+v.start.slice(11)+'–'+v.end.slice(11);
const eventSummary=v=>v?v.title+' · '+whenText(v)+(v.repeat!=='none'?(v.until?t('conflict.repeats_until',{date:fmt(v.until)}):t('conflict.repeats')):'')+(v.location?' · '+v.location:''):t('conflict.deleted');
const conflictText=(op,v)=>op.op==='event.save'?eventSummary(v):isHTML(op)?plainText(String(v).replace(/<\/(p|h2|h3|li)>/gi,'$&\n').replace(/<br\s*\/?>/gi,'\n')).trim():v;
function conflictTarget(op){
  if(op.op==='week.notes')return {key:op.week+'|'+op.project_id};
  if(op.op==='subtask.text'){for(const x of S.tasks){const s=x.subtasks.find(y=>y.id===op.id);if(s)return {t:x,s}}return null}
  const x=liveTask(op.id);return x?{t:x}:null;
}
const localValue=(op,a)=>op.op==='week.notes'?S.notes[a.key]||'':op.op==='subtask.text'?a.s.text:op.op==='task.title'?a.t.title:a.t.description;
function setLocal(op,a,v,rev){
  if(op.op==='week.notes'){S.notes[a.key]=v;S.notesRev[a.key]=rev;persist(op.week,op.project_id);return}
  if(op.op==='subtask.text'){a.s.text=v;a.s.rev=rev}
  else if(op.op==='task.title'){a.t.title=v;a.t.rev.title=rev}
  else{a.t.description=v;a.t.rev.notes=rev}
  persistTask(a.t);
}
function conflictHTML(k){
  const c=conflicts.get(k);if(!c)return '';
  const show=v=>isHTML(c.op)?'<div class="conflict-text conflict-html">'+sanitizeHTML(v)+'</div>':'<div class="conflict-text">'+esc(v)+'</div>';
  if(!c.choice)return '<div class="conflict" role="alert"><p>'+t('conflict.text_changed')+'</p><p class="conflict-label">'+t('conflict.other_version')+'</p>'+show(c.value)
    +'<div class="conflict-actions">'+btn('conflict-mine',t('conflict.keep_mine'),k,'primary')+btn('conflict-other',t('conflict.use_other'),k,'ghost')+'</div></div>';
  return '<div class="conflict"><div class="conflict-top"><p class="conflict-label">'+t('conflict.discarded')+'</p>'+btn('conflict-close',icons.x,k,'icon-btn',t('common.close_notice'))+'</div>'+show(c.discarded)
    +'<div class="conflict-actions">'+btn('conflict-copy',t('conflict.copy'),k,'ghost')+'</div></div>';
}
data.onConflict((op,value,rev)=>{
  if(!S)return;
  if(op.op==='event.save'){
    conflicts.set(conflictKey(op),{op,value,rev,choice:'',discarded:''});
    if(screen==='calendar'&&draft?.id===op.id){drawCalendar();return}
    toast(t('conflict.in',{title:op.title}),()=>showEventConflict(op),t('conflict.view'));
    return;
  }
  const a=conflictTarget(op);if(!a)return;
  conflicts.set(conflictKey(op),{op,value,rev,choice:'',discarded:''});
  const open=op.op==='week.notes'?!pane&&week===op.week&&project===op.project_id:pane?.id===a.t.id;
  if(open){drawDetail();return}
  if(op.op==='week.notes')toast(t('conflict.in_week_notes'),()=>goTo(op.week,op.project_id),t('conflict.view'));
  else toast(t('conflict.in',{title:titleOf(a.t)}),()=>gotoTask(a.t.id),t('conflict.view'));
});
function eventConflictHTML(k){
  const c=conflicts.get(k);if(!c)return '';
  if(!c.choice)return '<div class="conflict" role="alert"><p>'+(c.value?t('conflict.event_changed'):t('conflict.event_deleted'))+'</p>'
    +(c.value?'<p class="conflict-label">'+t('conflict.other_version')+'</p><div class="conflict-text">'+esc(eventSummary(c.value))+'</div>':'')
    +'<div class="conflict-actions">'+btn('conflict-mine',t('conflict.keep_mine'),k,'primary')+btn('conflict-other',c.value?t('conflict.use_other'):t('conflict.accept_delete'),k,'ghost')+'</div></div>';
  return '<div class="conflict"><div class="conflict-top"><p class="conflict-label">'+t('conflict.discarded')+'</p>'+btn('conflict-close',icons.x,k,'icon-btn',t('common.close_notice'))+'</div><div class="conflict-text">'+esc(eventSummary(c.discarded))+'</div>'
    +'<div class="conflict-actions">'+btn('conflict-copy',t('conflict.copy'),k,'ghost')+'</div></div>';
}
/* Opens the calendar on the event's week, with the editor on the local version. */
async function showEventConflict(op){
  screen='calendar';
  if(!await goTo(weekOf(op.start.slice(0,10))))return;
  draft=eventFromAPI({...op,rev:op.base_rev});deleteEvent='';drawCalendar();
}
async function resolveEvent(k,c,mine){
  await data.discard(c.op);
  /* The local version is the one the operation tried to write; the agenda in memory may already be the server's. */
  const local=eventFromAPI({...c.op,rev:c.op.base_rev});
  if(mine){
    local.rev=c.rev;S.events=[...S.events.filter(x=>x.id!==local.id),local];
    data.enqueue({op:'event.save',...eventToAPI(local),rev:undefined,base_rev:c.rev});
    c.discarded=c.value;if(draft?.id===local.id)draft=clone(local);
  }else{
    c.discarded=eventToAPI(local);
    S.events=S.events.filter(x=>x.id!==local.id);
    if(c.value){const e=eventFromAPI(c.value);S.events.push(e);if(draft?.id===e.id)draft=clone(e)}
  }
  c.choice=mine?'mine':'other';
  storeAgenda();
  if(!c.value&&!mine){if(draft?.id===c.op.id)draft=null;toast(t('conflict.discarded_toast',{summary:eventSummary(c.discarded)}));conflicts.delete(k)}
  if(screen==='calendar')drawCalendar();
}
async function resolveConflict(k,mine){
  const c=conflicts.get(k);if(!c||c.choice)return;
  if(c.op.op==='event.save')return resolveEvent(k,c,mine);
  if(mine)flushEdits();else if(ed){ed.notesDirty=false;ed.titleDirty=false}
  const a=conflictTarget(c.op);
  if(!a){conflicts.delete(k);drawDetail();return}
  await data.discard(c.op);
  const local=localValue(c.op,a);
  if(mine){setLocal(c.op,a,local,c.rev);data.enqueue({...c.op,value:local,base_rev:c.rev});c.discarded=c.value}
  else{setLocal(c.op,a,c.value,c.rev);c.discarded=local}
  c.choice=mine?'mine':'other';
  drawList();drawDetail();
}
data.onRev((op,rev)=>{
  if(!S)return;
  if(op.op==='event.save'){
    const e=S.events.find(x=>x.id===op.id);if(e)e.rev=rev;if(draft?.id===op.id)draft.rev=rev;
    storeAgenda();return;
  }
  if(op.op==='week.notes'){S.notesRev[op.week+'|'+op.project_id]=rev;persist(op.week,op.project_id);return}
  const a=conflictTarget(op);if(!a)return;
  if(a.s)a.s.rev=rev;else a.t.rev[op.op==='task.title'?'title':'notes']=rev;
  persistTask(a.t);
});

/* ---------- Account: login, signup, password and profile ---------- */
const timezone=()=>{try{return Intl.DateTimeFormat().resolvedOptions().timeZone||'UTC'}catch(_){return 'UTC'}};
const FIELDS=['email','password','timezone'];
function renderAuth(mode,message=''){
  clearInterval(tickTimer);
  /* Before logging in, the browser's language (so a message comes as a function, read after the switch). */
  setLanguage('auto');
  if(typeof message==='function')message=message();
  const link=(m,l)=>'<button type="button" class="quiet" data-act="auth" data-screen="'+m+'">'+l+'</button>';
  const password=auto=>field('password',t('auth.password'),'','password','required minlength="8" autocomplete="'+auto+'" aria-describedby="password-hint"')+'<p class="hint" id="password-hint">'+t('auth.password_hint')+'</p>';
  const lang='?lang='+language();
  const screens={
    login:[t('auth.login'),'<form id="login-form">'+field('email',t('auth.email'),'','email','required autocomplete="email"')+field('password',t('auth.password'),'','password','required autocomplete="current-password"')
      +'<p class="error" role="alert"></p><button class="primary">'+t('auth.login')+'</button></form><p class="auth-links">'+link('signup',t('auth.signup'))+link('forgot',t('auth.forgot'))+'</p>'],
    signup:[t('auth.signup'),'<form id="signup-form">'+field('email',t('auth.email'),'','email','required autocomplete="email"')+password('new-password')
      +'<p class="auth-legal">'+t('auth.legal',{terms:'/terms'+lang,privacy:'/privacy'+lang})+'</p>'
      +'<p class="error" role="alert"></p><button class="primary">'+t('auth.signup')+'</button></form><p class="auth-links">'+link('login',t('auth.have_account'))+'</p>'],
    forgot:[t('auth.reset_title'),'<form id="forgot-form"><p class="hint">'+t('auth.reset_hint')+'</p>'+field('email',t('auth.email'),'','email','required autocomplete="email"')
      +'<p class="error" role="alert"></p><button class="primary">'+t('auth.send_link')+'</button></form><p class="auth-links">'+link('login',t('auth.back_login'))+'</p>'],
    password:[t('auth.new_password'),'<form id="password-form">'+password('new-password')+'<p class="error" role="alert"></p><button class="primary">'+t('auth.save_password')+'</button></form>']
  };
  const [title,body]=screens[mode];
  $('#app').innerHTML='<main class="auth"><div class="auth-box"><p class="brand" aria-hidden="true">semana<span class="brand-dot">.</span></p><h1>'+title+'</h1>'
    +(message?'<p class="auth-notice" role="status">'+esc(message)+'</p>':'')+body+'</div></main>';
  $('#app input')?.focus();
}
async function submitAuth(form){
  const f=form.elements,error=form.querySelector('.error'),button=form.querySelector('button.primary');
  const fail=(m,name)=>{error.innerHTML=m;const i=name&&f[name];if(i){i.setAttribute('aria-invalid','true');i.focus()}};
  error.textContent='';button.disabled=true;
  try{
    if(form.id==='forgot-form'){
      const r=await data.api('POST','/api/password/request',{email:f.email.value.trim(),language:language()});
      if(r.status===422)return fail(esc(t('field.email')),'email');
      form.outerHTML='<p class="auth-notice" role="status">'+t('auth.link_sent')+'</p>';return;
    }
    if(form.id==='password-form'){
      const r=await data.api('POST','/api/password/reset',{token:resetToken,password:f.password.value});
      if(r.status===204){form.outerHTML='<p class="auth-notice" role="status">'+t('auth.password_changed')+'</p><p class="auth-links"><a href="/">'+t('auth.login')+'</a></p>';return}
      if(r.status===422)return fail(esc(t('field.password')),'password');
      form.outerHTML='<p class="auth-notice" role="alert">'+t('auth.link_invalid')+'</p><p class="auth-links"><button type="button" class="quiet" data-act="auth" data-screen="forgot">'+t('auth.another_link')+'</button></p>';return;
    }
    const signup=form.id==='signup-form',body={email:f.email.value.trim(),password:f.password.value};
    if(signup){body.timezone=timezone();body.language=language()}
    let r;
    try{r=await data.api('POST',signup?'/api/account':'/api/login',body)}
    catch(e){if(e.kind==='session')return fail(esc(t('auth.wrong_credentials')));throw e}
    if(r.status===200||r.status===201)return enter();
    const j=r.json||{};
    if(j.error==='email_taken')return fail(esc(t('auth.email_taken'))+' <button type="button" class="quiet" data-act="auth" data-screen="forgot">'+t('auth.forgot_q')+'</button>','email');
    if(j.error==='locked')return fail(esc(t('auth.locked',{time:new Date(j.retry_at).toLocaleTimeString(language(),{hour:'2-digit',minute:'2-digit'})})));
    if(j.error==='invalid'){const c=(j.fields||[]).find(x=>FIELDS.includes(x));return fail(esc(c?t('field.'+c):t('auth.check')),c)}
    fail(esc(t('auth.failed')));
  }catch(e){fail(esc(e.kind==='network'?t('auth.offline'):t('auth.failed')))}
  finally{button.disabled=false}
}
/* No session: login screen; with stored pending changes, says they wait for the account to log in again (FR-059). */
async function loginScreen(e){
  S=null;ed=null;pane=null;
  if(e.kind==='session'){const n=await data.pending();renderAuth('login',()=>n?t('auth.expired',{n}):'');return}
  renderAuth('login',()=>e.kind==='network'?t('auth.offline_login'):t('auth.open_failed'));
}
data.onImageRejected(reason=>toast(t('image.'+reason)));
data.onSession(()=>{if(S){flushEdits();loginScreen({kind:'session'})}});
function init(r){
  const {offline,...rest}=r;startInfo=rest;account=r.account;appearance.apply(account.appearance);setLanguage(account.language);
  if(!offline)offset=Date.parse(r.now)-Date.now();
  S={week:r.current_week,projects:r.projects.map(p=>({id:p.id,name:p.name})),tasks:[],notes:{},notesRev:{},snapshots:{},events:[],dues:[],agendaWeek:null};
}
async function enter(){
  let r;
  try{r=await data.start()}catch(e){loginScreen(e);return}
  init(r);week=S.week;pane=null;profileView='';notice='';addingProject=false;conflicts.clear();
  storage=storageLabel(data.state());
  const exists=id=>S.projects.some(p=>p.id===id);
  project=exists(remembered('project'))?remembered('project'):S.projects[0].id;
  screen='tasks';filter=exists(remembered('visibility'))?remembered('visibility'):'';draft=null;deleteEvent='';
  try{await load(project,week);await loadAgenda(week)}catch(e){if(e.kind==='session'){loginScreen(e);return}notice=t('week.offline')}
  render();
  clearInterval(tickTimer);tickTimer=setInterval(tick,60000);
  /* Only this account's queue is sent; another account's stays stored without being shown (FR-058). */
  data.send();
}
async function askLogout(){
  flushEdits();
  profilePending=await data.pending();
  if(profilePending){profileView='logout';drawProfile();$('#profile-pop .danger')?.focus();return}
  logout();
}
async function logout(){
  try{await data.api('POST','/api/logout')}catch(e){if(e.kind==='network'){toast(t('profile.logout_offline'));return}}
  const id=account.id;S=null;ed=null;pane=null;
  await data.clearAccount(id);
  renderAuth('login');
}
async function deleteAccount(form){
  const error=form.querySelector('.error');error.textContent='';
  let r;
  try{r=await data.api('DELETE','/api/account',{password:form.elements.password.value})}
  catch(e){if(e.kind==='session')return loginScreen(e);error.textContent=t('profile.delete_offline');return}
  if(r.status===403){error.textContent=t('profile.wrong_password');form.elements.password.select();return}
  if(r.status!==204){error.textContent=t('profile.delete_failed');return}
  const id=account.id;S=null;ed=null;pane=null;
  await data.clearAccount(id);appearance.forget();
  renderAuth('login',()=>t('profile.deleted'));
}

/* ---------- Interface events ---------- */
document.addEventListener('click',e=>{
  for(const d of document.querySelectorAll('details[open]'))if(!d.contains(e.target))d.open=false;
  if(linkCtx&&!e.target.closest?.('#link-form,[data-fmt="link"],[data-act="link-edit"]'))closeLinkForm(false);
  if(ignoreClick&&e.target.closest?.(BLOCK)){e.stopPropagation();return}
  if($('#series-pop')&&!e.target.closest('#series-pop')){e.stopPropagation();e.preventDefault();closeSeries(true)}
},true);

/* Profile menu opened from the notes: when it closes without going elsewhere, the caret comes back (004 FR-002). */
let profileFromNotes=false;
document.addEventListener('focusin',e=>{if(e.target.matches?.('.profile-menu summary')&&e.relatedTarget&&e.relatedTarget===ed?.notes)profileFromNotes=true});
document.addEventListener('toggle',e=>{
  if(!e.target.matches?.('.profile-menu')||e.target.open)return;
  if(profileView||backupFile){profileView='';backupFile=null;drawProfile()}
  const a=document.activeElement;
  if(profileFromNotes&&ed&&(a===document.body||e.target.contains(a))){
    const r=lastRange;ed.notes.focus({preventScroll:true});
    if(r&&ed.notes.contains(r.commonAncestorContainer))setCaret(r);
  }
  profileFromNotes=false;
},true);
document.addEventListener('mousedown',e=>{if(e.target.closest?.('.fmt-bar [data-fmt],.size-menu>summary,.link-bubble button,.so'))e.preventDefault()});
document.addEventListener('mousemove',e=>{
  const o=search&&e.target.closest?.('.so');if(!o||+o.dataset.i===search.sel)return;
  search.sel=+o.dataset.i;
  for(const li of document.querySelectorAll('.so'))li.setAttribute('aria-selected',String(li===o));
  $('#search-input')?.setAttribute('aria-activedescendant',o.id);
});

document.addEventListener('click',e=>{
  const au=e.target.closest?.('[data-act="auth"]');if(au){renderAuth(au.dataset.screen);return}
  if(!S)return;
  if(search){
    if(e.target.id==='search'){closeSearch(true);return}
    const o=e.target.closest?.('.so');if(o){chooseResult(+o.dataset.i);return}
    if(e.target.closest?.('#search'))return;
  }
  const link=e.target.closest?.('#notes a[href]');
  if(link&&(e.ctrlKey||e.metaKey||ed?.read)){e.preventDefault();openLink(link.getAttribute('href'));return}
  if(ed&&!ed.read&&e.target.classList&&['doc-page','doc','p-notes'].some(c=>e.target.classList.contains(c))){clickToNotes(e);return}
  const f=e.target.closest?.('[data-fmt]');
  if(f){format(f.dataset.fmt,f.dataset.value);if(f.dataset.fmt==='block'){const m=$('#size-menu');if(m)m.open=false}return}
  const el=e.target.closest?.('[data-act]');if(!el)return;
  const a=el.dataset.act,id=el.dataset.id;
  switch(a){
    case 'home':screen='tasks';draft=null;goTo(S.week);return;
    case 'today':draft=null;goTo(S.week);return;
    case 'tasks':case 'calendar':flushEdits();show(null);screen=a;draft=null;addingProject=false;
      if(a==='calendar'&&S.agendaWeek!==week)loadAgenda(week).then(render,e=>loginScreen(e));else render();return;
    case 'prev':case 'next':draft=null;goTo(addDays(week,a==='prev'?-7:7));return;
    case 'dismiss':notice='';$('.notice')?.remove();return;
    case 'new-task':newTask();return;
    case 'new-project':flushEdits();addingProject=true;drawToolbar();$('#project-form input')?.focus();return;
    case 'cancel-project':addingProject=false;drawToolbar();return;
    case 'task':{
      if(performance.now()<suppressUntil)return;
      const fromCard=el.classList.contains('task-card');
      if(pane?.id===id){if(fromCard)closeTask();return}
      show({id});drawList();drawDetail();
      if(fromCard)cardFor(id)?.focus({preventScroll:true});
      if(isMobile()){const d=$('#detail'),r=d.getBoundingClientRect();if(r.top>innerHeight*.6||r.top<0)d.scrollIntoView({behavior:'smooth',block:'start'})}
      return;
    }
    case 'flag':{const x=editable();if(!x)return;x.important=!x.important;touch(x);persistTask(x);data.enqueue({op:'task.important',id:x.id,value:x.important});const l=x.important?t('task.unmark_important'):t('task.mark_important');el.setAttribute('aria-pressed',String(x.important));el.setAttribute('aria-label',l);el.title=l;drawList();return}
    case 'ask-delete-task':setConfirm(true);return;
    case 'cancel-delete-task':setConfirm(false);return;
    case 'delete-task':{flushEdits();const x=liveTask(id);S.tasks=S.tasks.filter(y=>y.id!==id);confirmTask=false;pane=null;if(x){persistTask(x);syncDue(x,true)}data.enqueue({op:'task.delete',id});drawList();drawDetail();toast(t('task.deleted',{title:x?titleOf(x):''}));return}
    case 'sub-done':{const x=editable();if(!x||!setDone(x,id,true))return;refreshSubs(x);srSay(t('subtask.completed'));toast(t('subtask.completed'),()=>{setDone(x,id,false);afterSubChange(x)});return}
    case 'sub-reopen':{const x=editable();if(!x||!setDone(x,id,false))return;refreshSubs(x);return}
    case 'sub-del':{const x=editable();if(x)deleteSub(x,id);return}
    case 'dash-done':{if(readOnly())return;const x=liveTask(el.dataset.task);if(!x||!setDone(x,id,true))return;drawList();drawDetail();toast(t('subtask.completed'),()=>{setDone(x,id,false);afterSubChange(x)});return}
    case 'open-task':openTask(id);return;
    case 'search':openSearch();return;
    case 'due-pick':{
      const inp=$('#due-input');if(!inp||!editable())return;
      /* From the keyboard (detail 0), the field shows up to type the date; with mouse or touch, the picker opens. */
      if(e.detail!==0)try{if(typeof inp.showPicker==='function'){inp.showPicker();return}}catch(_){}
      inp.classList.add('show');inp.tabIndex=0;inp.focus();return;
    }
    case 'due-clear':{const x=editable();if(!x)return;setDue(x,'');$('.due-chip')?.focus();return}
    case 'open-location':{const r=parseLink($('#event-form [name="location"]')?.value);if(r.href)openLink(r.href);return}
    case 'new-event':openEvent('');return;
    case 'event':if(ignoreClick)return;openEvent(id,'','',el.dataset.occ);return;
    case 'delete-occ':{const e=S.events.find(x=>x.id===id);if(!e||!draft?.occurrence)return;const occ=draft.occurrence;draft=null;deleteEvent='';submitEvent({...clone(e),except:[...(e.except||[]),occ]});toast(t('event.deleted_day'));return}
    case 'series-one':case 'series-all':{const fn=seriesActions?.[a==='series-one'?'one':'series'];closeSeries();fn?.();return}
    case 'series-cancel':closeSeries(true);return;
    case 'slot':openEvent('',el.dataset.day,el.dataset.time);return;
    case 'close-event':draft=null;drawCalendar();return;
    case 'ask-delete-event':deleteEvent=id;drawCalendar();return;
    case 'cancel-delete':deleteEvent='';drawCalendar();return;
    case 'delete-event':S.events=S.events.filter(x=>x.id!==id);conflicts.delete('event.save|'+id);data.enqueue({op:'event.delete',id});draft=null;storeAgenda();drawCalendar();toast(t('event.deleted'));return;
    case 'undo':{const fn=toastUndo;hideToast();if(fn)fn();return}
    case 'link-cancel':closeLinkForm(true);return;
    case 'link-unlink':{const anchor=linkCtx?.anchor;closeLinkForm(true);unlink(anchor);return}
    case 'link-open':if(bubbleLink)openLink(bubbleLink.getAttribute('href'));return;
    case 'link-copy':if(bubbleLink)copyPath(bubbleLink.getAttribute('href'),false);return;
    case 'link-edit':if(bubbleLink)openLinkForm(bubbleLink);return;
    case 'link-remove':unlink(bubbleLink);return;
    case 'pref':setPref(el.dataset.pref,el.dataset.value);return;
    case 'language':setLanguagePref(el.dataset.value);return;
    case 'export':el.closest('details').open=false;exportBackup();return;
    case 'import':if(!navigator.onLine){toast(t('backup.import_offline'));return}$('#import').click();return;
    case 'import-confirm':importBackup();return;
    case 'import-cancel':backupFile=null;drawProfile();$('#profile-pop [data-act="export"]')?.focus();return;
    case 'logout':askLogout();return;
    case 'logout-confirm':logout();return;
    case 'delete-account':profileView='delete';drawProfile();$('#delete-form input')?.focus();return;
    case 'profile-back':profileView='';drawProfile();$('#profile-pop button')?.focus();return;
    case 'conflict-mine':case 'conflict-other':resolveConflict(id,a==='conflict-mine');return;
    case 'conflict-copy':{const c=conflicts.get(id);if(c)copyText(conflictText(c.op,c.discarded)).then(ok=>toast(ok?t('conflict.copied'):t('conflict.copy_failed')));return}
    case 'conflict-close':conflicts.delete(id);if(screen==='calendar')drawCalendar();else drawDetail();return;
  }
});

document.addEventListener('submit',e=>{
  const form=e.target;if(!form.id)return;e.preventDefault();
  if(['login-form','signup-form','forgot-form','password-form'].includes(form.id)){submitAuth(form);return}
  if(!S)return;
  if(form.id==='sub-form'){addSubtask(form);return}
  if(form.id==='link-form'){applyLink(form);return}
  if(form.id==='event-form'){saveEvent(form);return}
  if(form.id==='delete-form'){deleteAccount(form);return}
  if(form.id==='project-form'){
    const input=form.elements.name,name=input.value.trim();
    const fail=m=>{input.setCustomValidity(m);input.reportValidity()};
    if(!name)return fail(t('project.name_required'));
    if(S.projects.some(p=>p.name.toLowerCase()===name.toLowerCase()))return fail(t('project.name_taken'));
    show(null);const id=crypto.randomUUID();S.projects.push({id,name});
    data.enqueue({op:'project.create',id,name});storeStart();
    applyWeek(id,week,{state:stateOf(week),tasks:[],notes:{html:'',rev:0}});persist(week,id);
    project=id;addingProject=false;render();
  }
});

document.addEventListener('input',e=>{
  const el=e.target;
  if(search&&el.id==='search-input'){search.q=el.value;search.sel=0;rank();drawResults();return}
  if(el.closest?.('.auth')){el.removeAttribute('aria-invalid');const er=el.form?.querySelector('.error');if(er)er.textContent='';return}
  if(ed&&el===ed.notes){markNotesDirty();return}
  if(ed&&el===ed.title){
    if(/[\r\n]/.test(el.value))el.value=el.value.replace(/[\r\n]+/g,' ');
    autosize(el);liveTitle(el.value);ed.titleDirty=true;typing();clearTimeout(titleTimer);titleTimer=setTimeout(saveTitle,300);return;
  }
  if(el.classList?.contains('sub-text')){if(/[\r\n]/.test(el.value))el.value=el.value.replace(/[\r\n]+/g,' ');autosize(el);return}
  if(el.closest?.('#link-form')){const er=el.form.querySelector('.error');if(er)er.textContent='';return}
  if(el.closest?.('#project-form'))el.setCustomValidity('');
  if(el.closest?.('#event-form')){
    const er=el.form.querySelector('.error');if(er)er.textContent='';
    if(el.name==='location'){const b=$('[data-act="open-location"]');if(b)b.hidden=!parseLink(el.value).href}
    syncEventFrequency(el);
  }
});

document.addEventListener('focusout',e=>{
  if(!ed||ed.read)return;
  if(e.target===ed.notes){
    saveNotes();
    if(!e.relatedTarget?.closest?.('.link-bubble'))setTimeout(()=>{if(ed&&document.activeElement!==ed.notes)hideBubble()},0);
    /* When leaving the field, shows the already sanitized content (without leftover browser styles). */
    if(ed.edited&&document.hasFocus()&&!e.relatedTarget?.closest?.('.fmt-bar,.link-bubble,.search-layer,.profile-menu')){
      const html=toEditor(storedNotes());if(ed.notes.innerHTML!==html)ed.notes.innerHTML=html;ed.edited=false;lastRange=null;notesEmpty();
    }
  }else if(e.target===ed.title){
    saveTitle();const x=liveTask(ed.taskId);if(!x)return;
    const v=x.title.trim();if(v!==x.title){x.title=v;persistTask(x)}
    if(ed.title.value!==v){ed.title.value=v;autosize(ed.title)}
    liveTitle(v);
  }
});

document.addEventListener('selectionchange',()=>{
  if(!ed||ed.read)return;
  const s=getSelection();
  if(s.rangeCount&&ed.notes.contains(s.anchorNode))lastRange=s.getRangeAt(0).cloneRange();
  if(!toolbarFrame)toolbarFrame=requestAnimationFrame(()=>{toolbarFrame=0;if(!ed)return;if(selectionInNotes())updateToolbar();updateBubble()});
});

document.addEventListener('paste',e=>{
  if(!ed||ed.read||!ed.notes.contains(e.target))return;
  e.preventDefault();
  const files=[...(e.clipboardData.files||[])];
  if(files.length){insertImages(files);return}
  const html=e.clipboardData.getData('text/html'),text=e.clipboardData.getData('text/plain'),href=autoLink(text);
  if(href){
    const s=getSelection();
    if(s.rangeCount&&!s.getRangeAt(0).collapsed)document.execCommand('createLink',false,href);
    else document.execCommand('insertHTML',false,'<a href="'+esc(href)+'">'+esc(isFileLink(href)?fileName(href):text.trim())+'</a>');
  }else if(html){const clean=sanitizeHTML(html);if(clean)document.execCommand('insertHTML',false,toEditor(clean));else if(text)insertPlain(text)}
  else if(text)insertPlain(text);
  markNotesDirty();
});
document.addEventListener('dragover',e=>{if(ed&&!ed.read&&ed.notes.contains(e.target)&&e.dataTransfer?.types?.includes('Files'))e.preventDefault()});
document.addEventListener('drop',e=>{
  if(!ed||!ed.notes.contains(e.target)||!e.dataTransfer?.files?.length)return;
  e.preventDefault();
  if(ed.read)return;
  insertImages([...e.dataTransfer.files],caretFromPoint(e.clientX,e.clientY));
});

/* ---------- Images in notes (008) ---------- */
const IMAGE_TYPES=['image/jpeg','image/png','image/gif','image/webp'];
/* Longest side up to 1600 px; PNG stays PNG (screenshots with text), the rest becomes JPEG; GIF goes as it came. */
async function shrinkImage(file){
  if(file.type==='image/gif')return file.size<=5*1024*1024?{blob:file,mime:'image/gif'}:null;
  const bmp=await createImageBitmap(file),k=Math.min(1,1600/Math.max(bmp.width,bmp.height));
  if(k===1&&file.size<=1024*1024){bmp.close();return {blob:file,mime:file.type}}
  const c=document.createElement('canvas');c.width=Math.round(bmp.width*k);c.height=Math.round(bmp.height*k);
  c.getContext('2d').drawImage(bmp,0,0,c.width,c.height);bmp.close();
  const mime=file.type==='image/png'?'image/png':'image/jpeg',blob=await new Promise(r=>c.toBlob(r,mime,.85));
  return blob&&blob.size<=5*1024*1024?{blob,mime}:null;
}
async function insertImages(files,where){
  const target=ed;
  const ok=files.filter(f=>IMAGE_TYPES.includes(f.type)&&f.size<=20*1024*1024);
  if(ok.length<files.length)toast(t('image.types'));
  if(!ok.length)return;
  const html=[];
  for(const f of ok){
    let r=null;try{r=await shrinkImage(f)}catch(_){}
    if(!r){toast(t('image.unusable'));continue}
    const id=crypto.randomUUID();
    await data.storeImage(id,r.mime,r.blob);
    html.push('<img src="/api/images/'+id+'">');
  }
  if(!html.length||ed!==target)return;
  target.notes.focus({preventScroll:true});
  if(where){const s=getSelection();s.removeAllRanges();s.addRange(where)}
  else if(!selectionInNotes()&&lastRange&&target.notes.contains(lastRange.commonAncestorContainer))setCaret(lastRange);
  document.execCommand('insertHTML',false,html.join(''));
  markNotesDirty();
}
/* A just-pasted image may be requested before its upload ends (without the service worker in control):
   tries again a few times, with growing intervals. */
document.addEventListener('error',e=>{
  const img=e.target;
  if(img.tagName!=='IMG'||!img.closest('.notes')||!/^\/api\/images\//.test(img.getAttribute('src')))return;
  const n=Number(img.dataset.tries||0);if(n>=6)return;
  img.dataset.tries=n+1;
  setTimeout(()=>{if(img.isConnected)img.src=img.getAttribute('src')},500*2**n);
},true);
/* Right edge of the image: pulling changes the width (48 px up to the text width), keeping the aspect ratio. */
const onEdge=(img,x)=>x>img.getBoundingClientRect().right-12;
let resize=null;
document.addEventListener('pointermove',e=>{
  if(resize){
    const w=Math.round(Math.max(48,Math.min(resize.max,resize.w+e.clientX-resize.x)));
    resize.img.setAttribute('width',w);return;
  }
  const img=e.target.closest?.('.notes[contenteditable="true"] img');
  if(img)img.style.cursor=onEdge(img,e.clientX)?'ew-resize':'';
});
document.addEventListener('pointerdown',e=>{
  const img=e.target.closest?.('.notes[contenteditable="true"] img');
  if(!img||!ed||ed.read||!onEdge(img,e.clientX))return;
  e.preventDefault();
  resize={img,x:e.clientX,w:img.getBoundingClientRect().width,max:ed.notes.clientWidth};
  img.classList.add('resizing');img.setPointerCapture?.(e.pointerId);
});
document.addEventListener('pointerup',()=>{
  if(!resize)return;
  resize.img.classList.remove('resizing');resize=null;markNotesDirty();
});

document.addEventListener('keydown',e=>{
  if(!S)return;
  const el=e.target;
  if(e.ctrlKey&&!e.metaKey&&!e.altKey&&!e.shiftKey&&(e.code==='Space'||e.key===' ')){e.preventDefault();openSearch();return}
  if(search){
    const n=search.res.list.length;
    if(e.key==='Escape'){e.preventDefault();closeSearch(true)}
    else if((e.key==='ArrowDown'||e.key==='ArrowUp')&&n){e.preventDefault();search.sel=(search.sel+(e.key==='ArrowDown'?1:-1)+n)%n;drawResults()}
    else if(e.key==='Enter'){e.preventDefault();chooseResult(search.sel)}
    else if(e.key==='Tab')e.preventDefault();
    return;
  }
  if(e.key==='Escape'){
    if(linkCtx){closeLinkForm(true);return}
    const open=[...document.querySelectorAll('details[open]')];
    if(open.length){for(const d of open){const had=d.contains(document.activeElement);d.open=false;if(had)d.querySelector('summary')?.focus()}return}
    if(bubbleLink){hideBubble();return}
    if(confirmTask){setConfirm(false);return}
    if(addingProject){addingProject=false;drawToolbar();return}
    if(el.classList?.contains('sub-text')){const s=current()?.subtasks.find(x=>x.id===el.dataset.sub);if(s)el.value=s.text;el.blur();return}
    if(el.id==='sub-new-input'&&el.value){el.value='';return}
    if(draft&&screen==='calendar'&&!el.closest?.('input,textarea,select')){draft=null;drawCalendar();return}
    if(screen==='tasks'&&pane&&!el.closest?.('#due-input,#project-form,select')){e.preventDefault();closeTask()}
    return;
  }
  if(ed&&!ed.read&&el===ed.title&&e.key==='Enter'){e.preventDefault();saveTitle();placeCaret(false);return}
  if(el.classList?.contains('sub-text')&&e.key==='Enter'){e.preventDefault();el.blur();return}
  if(ed&&!ed.read&&el===ed.notes){
    const mod=e.ctrlKey||e.metaKey;
    if(mod&&!e.shiftKey&&!e.altKey&&e.code==='KeyK'){e.preventDefault();openLinkForm();return}
    if(mod&&e.shiftKey&&e.code==='KeyH'){e.preventDefault();format('mark');return}
    if(mod&&e.shiftKey&&e.code==='Digit8'){e.preventDefault();format('list');return}
    if(mod&&e.altKey&&['Digit1','Digit2','Digit0'].includes(e.code)){e.preventDefault();format('block',{Digit1:'h2',Digit2:'h3',Digit0:'p'}[e.code]);return}
    if(mod&&!e.shiftKey&&e.code==='KeyU'){e.preventDefault();return}
  }
  if(el.classList?.contains('task-card')&&!readOnly()){
    if(e.altKey&&(e.key==='ArrowUp'||e.key==='ArrowDown')){e.preventDefault();moveByKeyboard(el,e.key==='ArrowUp'?-1:1);return}
    if((e.key==='ArrowLeft'||e.key==='ArrowRight')&&el.classList.contains('selected')){
      e.preventDefault();const x=liveTask(el.dataset.id);if(!x)return;
      const start=x.progress,step=e.shiftKey?10:5;setProgress(x,start+(e.key==='ArrowRight'?step:-step));commitProgress(x,start,true);
    }
  }
});

/* Card gestures: progress (horizontal, selected card) and order (vertical; on touch, after holding). */
document.addEventListener('pointerdown',e=>{
  const card=e.target.closest?.('.task-card');
  if(!card||!S||readOnly()||(e.pointerType==='mouse'&&e.button!==0))return;
  const x=liveTask(card.dataset.id);if(!x)return;
  gesture={t:x,card,pid:e.pointerId,touch:e.pointerType!=='mouse',x0:e.clientX,y0:e.clientY,x:e.clientX,y:e.clientY,start:x.progress,width:card.getBoundingClientRect().width,mode:'',timer:0};
  if(gesture.touch)gesture.timer=setTimeout(()=>{if(gesture&&!gesture.mode)beginSort()},HOLD_MS);
});
document.addEventListener('pointermove',e=>{
  const g=gesture;if(!g||e.pointerId!==g.pid)return;
  g.x=e.clientX;g.y=e.clientY;
  const dx=g.x-g.x0,dy=g.y-g.y0;
  if(!g.mode){
    if(Math.abs(dx)<(g.touch?8:5)&&Math.abs(dy)<(g.touch?8:5))return;
    clearTimeout(g.timer);
    const horizontal=Math.abs(dx)>Math.abs(dy);
    if(horizontal&&g.card.classList.contains('selected')){g.mode='progress';g.card.classList.add('dragging');try{g.card.setPointerCapture(g.pid)}catch(_){}}
    else if(!horizontal&&!g.touch)beginSort();
    else{gesture=null;return}
  }
  e.preventDefault();
  if(g.mode==='progress')setProgress(g.t,g.start+dx/g.width*100);
  else{moveSort();autoScroll()}
});
function endGesture(e){
  const g=gesture;if(!g||e.pointerId!==g.pid)return;
  gesture=null;clearTimeout(g.timer);cancelAnimationFrame(scrollFrame);scrollFrame=0;
  if(g.mode==='progress'){g.card.classList.remove('dragging');commitProgress(g.t,g.start,false);suppressUntil=performance.now()+350}
  else if(g.mode==='sort'){document.body.classList.remove('is-sorting');finishSort(g);suppressUntil=performance.now()+350}
}
document.addEventListener('pointerup',endGesture);
document.addEventListener('pointercancel',endGesture);
/* During a gesture, touch neither scrolls the page nor opens the context menu. */
document.addEventListener('touchmove',e=>{if(gesture&&gesture.mode)e.preventDefault()},{passive:false});
document.addEventListener('contextmenu',e=>{if(gesture&&gesture.touch)e.preventDefault()});

document.addEventListener('change',e=>{
  const el=e.target;if(!S)return;
  if(el.id==='import'&&el.files?.[0]){readFile(el);return}
  if(el.id==='project'){if(screen==='calendar'){filter=el.value;remember('visibility',filter);draft=null;render()}else goTo(week,el.value);return}
  if(el.id==='due-input'){const x=editable();if(x&&(el.value===''||validDate(el.value)))setDue(x,el.value);return}
  if(el.name==='start'&&el.closest('#event-form')){adjustEnd(el);return}
  if(el.name==='repeat'&&el.closest('#event-form')){syncEventFrequency(el);return}
  /* Filling the whole day implies all day (and unchecking all day unchecks the other). */
  if(el.name==='fullDay'&&el.closest('#event-form')){
    const day=el.form.elements.allDay;
    if(el.checked&&!day.checked){day.checked=true;day.dispatchEvent(new Event('change',{bubbles:true}))}
    return;
  }
  if(el.name==='allDay'&&el.closest('#event-form')){
    if(!el.checked)el.form.elements.fullDay.checked=false;
    const ev=eventValues(el.form),start=ev.start.slice(0,10),end=ev.end.slice(0,10);
    if(!validDate(start)||!validDate(end)){el.checked=!el.checked;return}
    if(ev.allDay){ev.start=start+'T00:00';ev.end=addDays(end,1)+'T00:00'}else{ev.start=start+'T09:00';ev.end=end+'T10:00'}
    draft=ev;drawCalendar();return;
  }
  if(el.id==='week'){if(validDate(el.value))goTo(weekOf(el.value));return}
  if(el.classList.contains('sub-text')){
    const x=editable(),s=x?.subtasks.find(y=>y.id===el.dataset.sub);if(!s)return;
    const v=el.value.replace(/\s+/g,' ').trim().slice(0,300);
    if(!v){el.value=s.text;return}
    el.value=v;
    if(v!==s.text){s.text=v;touch(x);persistTask(x);data.enqueue({op:'subtask.text',id:s.id,value:v,base_rev:s.rev});el.closest('.subtask')?.querySelector('.check')?.setAttribute('aria-label',t('subtask.complete',{text:v}))}
  }
});

/* ---------- Weekly rollover: the server processes it; the client notices the change within 1 minute (FR-047) ---------- */
/* Now in the account's time zone, by the server's clock. */
function localNow(){
  const p={};
  for(const x of new Intl.DateTimeFormat('en-CA',{timeZone:account.timezone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date(Date.now()+offset)))p[x.type]=x.value;
  return p.year+'-'+p.month+'-'+p.day+'T'+p.hour+':'+p.minute;
}
function today(){
  const p={};
  for(const x of new Intl.DateTimeFormat('en-CA',{timeZone:account.timezone,year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(Date.now()+offset)))p[x.type]=x.value;
  return p.year+'-'+p.month+'-'+p.day;
}
const weekNow=()=>weekOf(today());
async function tick(){
  if(!S||weekNow()===S.week)return;
  let r;try{r=await data.start()}catch(_){return}
  if(!S||r.current_week===S.week)return;
  flushEdits();
  const prev=S.week,w=week===prev?r.current_week:week;
  init(r);pane=null;
  try{await load(project,w);await loadAgenda(w)}catch(_){}
  if(!S)return;
  week=w;draft=null;notice=t('week.rollover');render();
}
/* Back on the tab: rollover and what changed on another device (FR-060). */
async function onReturn(){
  await tick();
  /* Appearance and language changed on another device (004 R4). */
  try{const r=await data.start();if(S){account=r.account;startInfo={...startInfo,account};appearance.apply(account.appearance);drawProfile();relabel()}}catch(_){}
  // ponytail: no reload unless the queue is empty; merge per field if that bothers anyone
  if(!S||await data.pending())return;
  try{await load(project,week);await loadAgenda(week)}catch(_){return}
  if(!S)return;
  if(screen==='calendar'){if(!draft)drawCalendar()}else{drawList();drawDetail()}
}
document.addEventListener('visibilitychange',()=>{if(!S)return;if(document.hidden){flushEdits();data.send()}else onReturn()});
addEventListener('pagehide',()=>{if(S){flushEdits();data.sendUrgent();data.send()}});
addEventListener('resize',()=>{if(ed){autosize(ed.title);sizeSubs();updateBubble()}});

function boot(){
  setLanguage('auto');
  navigator.serviceWorker?.register('/sw.js').catch(()=>{});
  if(location.pathname==='/password'){resetToken=location.hash.slice(1);history.replaceState(null,'','/password');renderAuth('password');return}
  enter();
}
boot();
