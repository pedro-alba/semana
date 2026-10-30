/* Appearance (feature 004, R1): a classic script in <head> applies the browser's copy before the
   first paint. The CSP forbids inline scripts, and app.js, being a module, runs later. */
(()=>{
const VALUES={theme:['graphite','paper','ink'],mode:['light','dark','system'],font:['theme','mono','sans','serif'],palette:['classic','sunset','lavender','moss','traffic','neutral']};
const DEFAULT={theme:'graphite',mode:'dark',font:'theme',palette:'classic'};
const ATTR={theme:'theme',mode:'mode-pref',font:'font',palette:'palette'};
const KEY='semana-appearance',root=document.documentElement,dark=matchMedia('(prefers-color-scheme: dark)');
const normalize=p=>Object.fromEntries(Object.keys(DEFAULT).map(k=>[k,VALUES[k].includes(p?.[k])?p[k]:DEFAULT[k]]));
const current=()=>normalize(Object.fromEntries(Object.entries(ATTR).map(([k,a])=>[k,root.getAttribute('data-'+a)])));
function mode(){
  const p=root.getAttribute('data-mode-pref'),m=p==='system'?(dark.matches?'dark':'light'):p;
  root.setAttribute('data-mode',m);
  document.querySelectorAll('.swatch').forEach(s=>s.setAttribute('data-mode',m));
}
function apply(p,keep=true){
  p=normalize(p);
  for(const k in ATTR)root.setAttribute('data-'+ATTR[k],p[k]);
  mode();
  if(keep)try{localStorage.setItem(KEY,JSON.stringify(p))}catch(_){}
}
function forget(){try{localStorage.removeItem(KEY)}catch(_){}apply(DEFAULT,false)}
dark.addEventListener?.('change',()=>{if(root.getAttribute('data-mode-pref')==='system')mode()});
let saved=null;try{saved=JSON.parse(localStorage.getItem(KEY))}catch(_){}
apply(saved,false);
window.appearance={VALUES,DEFAULT,normalize,apply,current,forget};
})();
