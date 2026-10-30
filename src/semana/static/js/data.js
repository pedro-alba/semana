/* Client data: API, cache and the operation queue in IndexedDB (R5, R6, R7).
   Only the current account's queue is read or sent (FR-058). */
/* Operations with a revision (R7; events, 002 R3): only one pending per target, with base_rev adjusted. */
const TEXT=new Set(['task.title','task.notes','subtask.text','week.notes','event.save','account.appearance','account.language']);
const target=op=>op.op==='week.notes'?op.project_id+'|'+op.week:op.op.startsWith('account.')?'':op.id;
const textKey=op=>TEXT.has(op.op)?op.op+'|'+target(op):'';
const BATCH=200;

let db=null,account=null,sending=false,again=false,sendTimer=0,retryTimer=0;
/* Every queue read and write runs in series, in call order. */
let chain=Promise.resolve();
const inOrder=f=>{const p=chain.then(f);chain=p.catch(()=>{});return p};
let current={kind:'saved',pending:0};
const inFlight=new Set();
const cb={state:()=>{},rev:()=>{},conflict:()=>{},session:()=>{},image:()=>{}};
export const onState=f=>{cb.state=f};
export const onRev=f=>{cb.rev=f};
export const onConflict=f=>{cb.conflict=f};
export const onSession=f=>{cb.session=f};
export const onImageRejected=f=>{cb.image=f};
export const state=()=>current;

/* ---------- IndexedDB ---------- */
const request=q=>new Promise((res,rej)=>{q.onsuccess=()=>res(q.result);q.onerror=()=>rej(q.error)});
async function open(){
  if(db)return db;
  db=await new Promise((res,rej)=>{
    const q=indexedDB.open('semana',3);
    q.onupgradeneeded=()=>{
      const d=q.result;
      /* Version 3 renamed every store and field: what older versions kept is dropped. */
      for(const n of [...d.objectStoreNames])d.deleteObjectStore(n);
      d.createObjectStore('cache',{keyPath:['account_id','key']});
      d.createObjectStore('queue',{autoIncrement:true}).createIndex('account_id','account_id');
      /* Pasted images not sent yet (008); the service worker reads them too. */
      d.createObjectStore('images',{keyPath:'id'}).createIndex('account_id','account_id');
    };
    q.onsuccess=()=>res(q.result);q.onerror=()=>rej(q.error);q.onblocked=()=>rej(Error('Database busy'));
  });
  return db;
}
const objectStore=async(name,mode='readonly')=>(await open()).transaction(name,mode).objectStore(name);
async function read(id,key){if(!id)return null;const r=await request((await objectStore('cache')).get([id,key]));return r?r.data:null}
export async function store(key,data){if(account)await request((await objectStore('cache','readwrite')).put({account_id:account,key,data}))}
/* An account's queued operations, in the order they were made. */
async function queue(id=account){
  const s=await objectStore('queue'),out=[];
  await new Promise((res,rej)=>{const q=s.index('account_id').openCursor(IDBKeyRange.only(id));q.onsuccess=()=>{const c=q.result;if(!c)return res();out.push({key:c.primaryKey,op:c.value.op});c.continue()};q.onerror=()=>rej(q.error)});
  return out;
}
const count=async(id=account)=>id?(await request((await objectStore('queue')).index('account_id').count(IDBKeyRange.only(id))))+(await request((await objectStore('images')).index('account_id').count(IDBKeyRange.only(id)))):0;
export async function pending(id=account){await chain;return count(id)}
const remove=async key=>request((await objectStore('queue','readwrite')).delete(key));

/* ---------- API ---------- */
export async function api(method,path,body){
  const init={method,credentials:'same-origin',headers:{}};
  if(method!=='GET'){init.headers['Content-Type']='application/json';init.body=JSON.stringify(body??{})}
  let r;
  try{r=await fetch(path,init)}catch(_){throw {kind:'network'}}
  let json=null;try{json=await r.json()}catch(_){}
  if(r.status===401)throw {kind:'session',json};
  return {status:r.status,json};
}
const readAccount=()=>{try{return localStorage.getItem('semana-account')}catch(_){return null}};

/* With no network, returns the cache of this browser's last account (with offline: true). */
export async function start(){
  let r;
  try{r=await api('GET','/api/start')}
  catch(e){
    account=readAccount();
    if(e.kind!=='network')throw e;
    const c=await read(account,'start');if(!c)throw e;
    await pendingSettings(c);
    updateState();
    return {...c,offline:true};
  }
  if(r.status!==200)throw {kind:'failed'};
  account=r.json.account.id;
  try{localStorage.setItem('semana-account',account)}catch(_){}
  /* Projects created here and not sent yet stay in the list. */
  const c=await read(account,'start');
  if(c&&await pending())for(const p of c.projects)if(!r.json.projects.some(x=>x.id===p.id))r.json.projects.push(p);
  await pendingSettings(r.json);
  await store('start',r.json);
  updateState();
  return r.json;
}
/* Appearance and language chosen and not sent yet beat the server's or the cache's (004 R3). */
async function pendingSettings(r){
  const ops=(await queue()).map(x=>x.op);
  const look=ops.findLast(x=>x.op==='account.appearance');
  if(look){const {op:_,...p}=look;r.account.appearance=p}
  const lang=ops.findLast(x=>x.op==='account.language');
  if(lang)r.account.language=lang.value;
}
/* With pending changes, the local copy beats the server's (FR-060). */
async function withCache(key,path){
  const local=async()=>await pending()?read(account,key):null;
  let c=await local();if(c)return c;
  let r;
  try{r=await api('GET',path)}
  catch(e){if(e.kind!=='network')throw e;c=await read(account,key);if(c)return c;throw {kind:'offline'}}
  if(r.status!==200)throw {kind:r.status===404?'not_found':'failed'};
  c=await local();if(c)return c;
  await store(key,r.json);
  return r.json;
}
export const week=(project,monday)=>withCache('week|'+project+'|'+monday,
  '/api/week?project='+encodeURIComponent(project)+'&week='+encodeURIComponent(monday));
/* Account search index (003 R1). With no network, uses the stored copy (or nothing) and says so with `offline`. */
export async function search(){
  try{const r=await api('GET','/api/search');if(r.status===200){await store('search',r.json);return r.json}}
  catch(e){if(e.kind!=='network')throw e}
  return {...(await read(account,'search')||{tasks:[],notes:[],events:[]}),offline:true};
}
/* The week's events and due dates, from every project (feature 002). */
export const agenda=monday=>withCache('agenda|'+monday,'/api/agenda?week='+encodeURIComponent(monday));

/* ---------- Queue ---------- */
function set(kind,n){current={kind,pending:n??current.pending};cb.state(current)}
async function updateState(){const n=await count();set(n?(current.kind==='offline'||current.kind==='failed'?current.kind:'saving'):(current.kind==='failed'?'failed':'saved'),n)}
/* Operations requested and not yet written to the queue (for the emergency send when the tab closes). */
const unwritten=new Set();
export const enqueue=op=>{unwritten.add(op);return inOrder(async()=>{
  if(!account)return;
  const k=textKey(op);
  /* A pending, unsent op on the same target: swap the content and keep its position and base_rev. */
  const same=k&&(await queue()).find(r=>!inFlight.has(r.key)&&textKey(r.op)===k);
  const s=await objectStore('queue','readwrite');
  if(same)await request(s.put({account_id:account,op:{...op,base_rev:same.op.base_rev}},same.key));
  else await request(s.add({account_id:account,op}));
  unwritten.delete(op);
  await updateState();
  schedule();
}).finally(()=>unwritten.delete(op))};
/* When the tab closes, the IndexedDB queue may not finish writing: what is only in memory goes straight out.
   Sending it again later changes nothing, because operations are idempotent (R6). */
export function sendUrgent(){
  if(!account||!unwritten.size)return;
  fetch('/api/ops',{method:'POST',keepalive:true,credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({account_id:account,ops:[...unwritten]})}).catch(()=>{});
}
/* Drops a field's unsent text (when resolving a conflict). */
export const discard=op=>inOrder(async()=>{
  const k=textKey(op);
  for(const r of await queue())if(!inFlight.has(r.key)&&textKey(r.op)===k)await remove(r.key);
  await updateState();
});
function schedule(ms=300){clearTimeout(sendTimer);sendTimer=setTimeout(send,ms)}
function retry(){clearTimeout(retryTimer);retryTimer=setTimeout(send,15000)}

/* ---------- Images (008) ---------- */
export async function storeImage(id,mime,blob){
  if(!account)return;
  await request((await objectStore('images','readwrite')).put({id,account_id:account,mime,blob}));
  updateState();schedule(0);
}
/* Sends the account's pending images; false if the network failed, 'session' if the session dropped. */
async function sendImages(){
  const list=await request((await objectStore('images')).index('account_id').getAll(IDBKeyRange.only(account)));
  for(const im of list){
    let r;
    try{r=await fetch('/api/images/'+im.id,{method:'PUT',credentials:'same-origin',headers:{'Content-Type':im.mime},body:im.blob})}catch(_){return false}
    if(r.status===401){cb.session();return 'session'}
    if(r.status>=500)return false;
    /* 413 (limit) and 422 (invalid) do not get better by retrying: drop it and tell the user */
    if(r.status===413)cb.image((await r.json().catch(()=>({}))).error==='quota'?'quota':'too_large');
    else if(!r.ok&&r.status!==404)cb.image('failed');
    await request((await objectStore('images','readwrite')).delete(im.id));
  }
  return true;
}
addEventListener('online',()=>send());

// ponytail: if the tab closes mid-send, the next edit of the same field may raise a false conflict; record op ids on the server if that shows up
export async function send(){
  if(!account)return;
  if(sending){again=true;return}
  sending=true;again=false;clearTimeout(retryTimer);
  let failed=false;
  try{
    const im=await sendImages();
    if(im==='session')return;
    if(!im){set('offline',await count());retry();return}
    for(;;){
      const [batch,total]=await inOrder(async()=>{
        const all=await queue(),batch=[],seen=new Set();
        /* Two texts of the same field never go in the same batch: the second needs the first one's rev. */
        for(const r of all){
          if(batch.length>=BATCH)break;
          const k=textKey(r.op);if(k&&seen.has(k))break;
          if(k)seen.add(k);batch.push(r);
        }
        batch.forEach(r=>inFlight.add(r.key));
        return [batch,all.length];
      });
      if(!batch.length)break;
      set(current.kind==='offline'?'offline':'saving',total);
      let resp;
      try{resp=await api('POST','/api/ops',{account_id:account,ops:batch.map(r=>r.op)})}
      catch(e){
        inFlight.clear();
        if(e.kind==='session'){cb.session();return}
        set('offline',total);retry();return;
      }
      if(resp.status===409&&resp.json?.error==='wrong_account'){inFlight.clear();cb.session();return}
      if(resp.status!==200){inFlight.clear();set('failed',total);retry();return}
      await inOrder(async()=>{for(let i=0;i<batch.length;i++){
        const r=batch[i],res=resp.json.results[i]||{};
        await remove(r.key);inFlight.delete(r.key);
        if(res.status==='ok'&&res.rev!=null){
          /* The next edit of the same field starts from the revision just written. */
          const k=textKey(r.op),next=(await queue()).find(x=>textKey(x.op)===k);
          if(next)await request((await objectStore('queue','readwrite')).put({account_id:account,op:{...next.op,base_rev:res.rev}},next.key));
          cb.rev(r.op,res.rev);
        }else if(res.status==='conflict')cb.conflict(r.op,res.value,res.rev);
        else if(res.status==='invalid')failed=true;
      }});
      if(failed)set('failed');
    }
    set(failed?'failed':'saved',0);
  }finally{
    sending=false;
    if(again)schedule(0);
  }
}

export const clearAccount=id=>inOrder(async()=>{
  try{await caches.delete('semana-images')}catch(_){}
  for(const name of ['cache','queue','images']){
    const s=await objectStore(name,'readwrite');
    await new Promise((res,rej)=>{const q=s.openCursor();q.onsuccess=()=>{const c=q.result;if(!c)return res();if(c.value.account_id===id)c.delete();c.continue()};q.onerror=()=>rej(q.error)});
  }
  try{if(localStorage.getItem('semana-account')===id)localStorage.removeItem('semana-account')}catch(_){}
  if(account===id){account=null;set('saved',0)}
});
