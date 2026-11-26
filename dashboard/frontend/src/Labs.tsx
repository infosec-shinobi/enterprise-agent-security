import {useEffect,useState} from 'react';
import Manual from './Manual';
import {getLabs,type Lab,type Catalog} from './api';

function LabCard({lab}:{lab:Lab}){
 return <article className="lab-card">
  <small>{lab.id.toUpperCase()} · MANIFEST DISCOVERED</small>
  <h2>{lab.title}</h2><p>{lab.description}</p>
  <div className="lab-stats"><span><strong>{lab.scenarios.length}</strong> scenarios</span><span><strong>{lab.controls.length}</strong> mapped controls</span><span><strong>{lab.services.length}</strong> required services</span></div>
  <h3>Required services</h3><div className="tags">{lab.services.map(s=><span key={s}>{s}</span>)}</div>
  <details><summary>Scenarios and expected outcomes</summary>
   <ol>{lab.scenarios.map(s=><li key={s.id}><strong>{s.title}</strong><p>Expected HTTP {s.expected.http_status} · {s.controls.join(', ')}</p></li>)}</ol>
  </details>
  <details><summary>Mapped security controls</summary>
   {lab.controls.map(c=><div key={c.id} className="control-detail"><strong>{c.id} — {c.name}</strong><p>{c.objective}</p><small>Enforcement: {c.enforcement_point}</small></div>)}
  </details>
  <p>Manual guide: <code>{lab.manual_path}</code></p><Manual labId={lab.id}/>
  <small>Expected outcomes only. Execution and service health are not checked here.</small>
 </article>
}
export default function Labs(){
 const [catalog,setCatalog]=useState<Catalog|null>(null);
 const [error,setError]=useState(false);
 const [attempt,setAttempt]=useState(0);
 useEffect(()=>{
  const controller=new AbortController(); let active=true;
  setCatalog(null);setError(false);
  const timer=window.setTimeout(()=>controller.abort(),10000);
  getLabs(controller.signal).then(c=>{if(active)setCatalog(c)}).catch(()=>{if(active)setError(true)}).finally(()=>window.clearTimeout(timer));
  return ()=>{active=false;controller.abort();window.clearTimeout(timer)};
 },[attempt]);
 return <section className="lab-list">
  <div className="lab-heading"><h2>Lab catalog</h2><button onClick={()=>setAttempt(a=>a+1)}>Refresh labs</button></div>
  {error?<p role="alert">Lab catalog unavailable. Check the API and retry.</p>:!catalog?<p role="status">Loading lab manifests…</p>:<>
   {catalog.issues.length>0&&<div className="placeholder" role="alert"><strong>Some labs were excluded</strong><ul>{catalog.issues.map((i,n)=><li key={n}>{i.directory}: {i.reason}</li>)}</ul></div>}
   {catalog.labs.length===0?<p>No valid lab manifests discovered.</p>:catalog.labs.map(lab=><LabCard key={lab.id} lab={lab}/>)}
  </>}
 </section>
}
