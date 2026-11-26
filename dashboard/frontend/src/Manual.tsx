import {useEffect,useState} from 'react';
export default function Manual({labId}:{labId:string}){
 const [open,setOpen]=useState(false);
 const [guide,setGuide]=useState('');
 const [error,setError]=useState(false);
 useEffect(()=>{
  if(!open)return;
  const controller=new AbortController();let active=true;
  setGuide('');setError(false);
  const timer=window.setTimeout(()=>controller.abort(),5000);
  fetch('/api/v1/labs/'+encodeURIComponent(labId)+'/manual',{signal:controller.signal,cache:'no-store'})
   .then(r=>{if(!r.ok)throw Error();return r.text()})
   .then(t=>{if(active)setGuide(t)}).catch(()=>{if(active)setError(true)})
   .finally(()=>window.clearTimeout(timer));
  return ()=>{active=false;controller.abort();window.clearTimeout(timer)};
 },[open,labId]);
 return <section className="lab-card"><h3>Manual mode</h3>
  <p>Run commands yourself from the repository root. Use one shell variant per step. Never run manual Compose concurrently with Autopilot. Confirm project ownership before destructive reset. Do not paste tokens into logs.</p>
  <button onClick={()=>setOpen(v=>!v)}>{open?'Hide manual guide':'Open Bash / PowerShell guide'}</button>
  {open&&(error?<p role="alert">Manual unavailable. Close and reopen to retry.</p>:guide?<pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere',maxHeight:'65vh',overflow:'auto'}}>{guide}</pre>:<p role="status">Loading guide…</p>)}
 </section>
}
