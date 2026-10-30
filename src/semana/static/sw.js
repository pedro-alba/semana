/* Service worker: network first, local copy as a fallback, so the app opens offline (R5).
   /api responses do not go through here (their cache lives in IndexedDB, js/data.js), except images. */
const CACHE='semana-static';
self.addEventListener('install',e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(['/','/app.css','/js/app.js','/js/pure.js','/js/data.js','/js/appearance.js','/js/i18n.js'])).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',e=>{e.waitUntil(self.clients.claim())});
/* Images (008 R3): network first. Offline, the cached copy or, if not sent yet, the one in
   IndexedDB. A server 404 is never swapped for the cached copy (it may belong to another account);
   only for this browser's unsent image, which belongs to the logged-in account (logging out clears pending ones). */
function unsent(id){
  return new Promise(res=>{
    const q=indexedDB.open('semana');
    q.onerror=()=>res(null);
    q.onsuccess=()=>{
      const d=q.result;
      if(!d.objectStoreNames.contains('images')){d.close();return res(null)}
      const g=d.transaction('images').objectStore('images').get(id);
      g.onsuccess=()=>{d.close();res(g.result?new Response(g.result.blob,{headers:{'Content-Type':g.result.mime}}):null)};
      g.onerror=()=>{d.close();res(null)};
    };
  });
}
async function image(req,id){
  try{
    const r=await fetch(req);
    if(r.ok){const copy=r.clone();caches.open('semana-images').then(c=>c.put(req,copy))}
    if(r.status===404)return (await unsent(id))||r;
    return r;
  }catch(_){
    return (await caches.match(req,{cacheName:'semana-images'}))||(await unsent(id))||Response.error();
  }
}
self.addEventListener('fetch',e=>{
  const req=e.request,url=new URL(req.url);
  const img=req.method==='GET'&&url.origin===location.origin&&url.pathname.match(/^\/api\/images\/([0-9a-f-]{36})$/);
  if(img){e.respondWith(image(req,img[1]));return}
  if(req.method!=='GET'||url.origin!==location.origin||url.pathname.startsWith('/api'))return;
  e.respondWith(fetch(req).then(r=>{
    if(r.ok){const copy=r.clone();caches.open(CACHE).then(c=>c.put(req,copy))}
    return r;
  }).catch(()=>caches.match(req).then(r=>r||(req.mode==='navigate'?caches.match('/'):Response.error()))));
});
