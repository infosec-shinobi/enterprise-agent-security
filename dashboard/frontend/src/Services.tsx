import {useEffect,useState} from 'react';
import {getServices,type ServiceObservation} from './api';

export default function Services(){
 const [rows,setRows]=useState<ServiceObservation[]|null>(null);
 const [error,setError]=useState(false);
 const [attempt,setAttempt]=useState(0);
 const [busy,setBusy]=useState(true);
 useEffect(()=>{
  const controller=new AbortController();let active=true;
  setBusy(true);setRows(null);setError(false);
  const timer=window.setTimeout(()=>controller.abort(),8000);
  getServices(controller.signal).then(v=>{if(active)setRows(v)}).catch(()=>{if(active)setError(true)}).finally(()=>{window.clearTimeout(timer);if(active)setBusy(false)});
  return ()=>{active=false;controller.abort();window.clearTimeout(timer)};
 },[attempt]);
 return <section>
  <div className="lab-heading"><h2>Infrastructure health</h2><button disabled={busy} onClick={()=>{setBusy(true);setAttempt(a=>a+1)}}>Refresh services</button></div>
  <p>On-demand host-side observations. Availability is not security control effectiveness.</p>
  {busy?<p role="status">Checking services…</p>:error?<p role="alert">Service observations unavailable. Check the API or retry shortly.</p>:rows&&<>
   <div className="lab-stats">{(['available','unavailable','unknown'] as const).map(s=><span key={s}><strong>{rows.filter(r=>r.status===s).length}</strong> {s}</span>)}</div>
   <div className="cards service-grid">{rows.map(r=><article className="lab-card service-card" key={r.id}>
    <small>{r.id}</small><h2>{r.name}</h2><p>{r.role}</p>
    <strong className={'service-'+r.status}>{r.status.toUpperCase()}</strong>
    <p>{r.reason}</p><p>{r.endpoint||'Internal / no host probe'}</p>
    <p>{r.http_status===null?'No HTTP status':'HTTP '+r.http_status} · {r.duration_ms===null?'Not probed':r.duration_ms+' ms'}</p>
    <small>Observed: {new Date(r.checked_at).toLocaleString()}</small>
    <p>Control effectiveness: Not assessed</p>
   </article>)}</div>
  </>}
 </section>
}
