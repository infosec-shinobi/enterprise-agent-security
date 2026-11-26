import {useEffect,useState} from 'react';
import type {Control} from './api';
type Assertion={scenario:string;controls:string[];outcome:'pass'|'fail'|'error'|'not_run';expected:number;actual:number|null;reason:string};
type View={run_id:string;outcome:string;exit_code:number;cleanup:string;reason:string;duration_ms:number;manifest_matches:boolean;scenarios:Assertion[];controls:Control[];control_effectiveness:string};
export default function Results({runId}:{runId:string}){
 const [view,setView]=useState<View|null>(null);
 const [error,setError]=useState(false);
 const [attempt,setAttempt]=useState(0);
 useEffect(()=>{
  const controller=new AbortController();let active=true;
  setView(null);setError(false);
  const timer=window.setTimeout(()=>controller.abort(),5000);
  fetch('/api/v1/runs/'+encodeURIComponent(runId)+'/evidence',{signal:controller.signal,cache:'no-store'})
   .then(r=>{if(!r.ok)throw Error();return r.json()})
   .then((v:View)=>{if(v.run_id!==runId||!Array.isArray(v.scenarios)||!Array.isArray(v.controls)||v.control_effectiveness!=='not_assessed')throw Error();if(active)setView(v)})
   .catch(()=>{if(active)setError(true)}).finally(()=>window.clearTimeout(timer));
  return ()=>{active=false;controller.abort();window.clearTimeout(timer)};
 },[runId,attempt]);
 return <article className="lab-card">
  <div className="lab-heading"><h2>Validated evidence</h2><button onClick={()=>setAttempt(a=>a+1)}>Refresh evidence</button></div>
  {error?<p role="alert">Evidence unavailable or invalid. Inspect the local report.</p>:!view?<p role="status">Loading evidence…</p>:<>
   <h3>{view.outcome.toUpperCase()} — {view.reason}</h3>
   <p>Evidence exit code: {view.exit_code} · Cleanup: {view.cleanup} · Duration: {(view.duration_ms/1000).toFixed(1)}s</p>
   <p>{view.manifest_matches?'Current manifest matches evidence.':'Manifest differs or was unavailable at execution; current coverage not established.'}</p>
   <div className="lab-stats">{(['pass','fail','error','not_run'] as const).map(k=><span key={k}><strong>{view.scenarios.filter(s=>s.outcome===k).length}</strong> {k.replace('_',' ')}</span>)}</div>
   {view.scenarios.length===0&&<p>No scenario results recorded.</p>}
   {view.scenarios.map(s=><div key={s.scenario} className="control-detail"><strong>{s.scenario} — {s.outcome.toUpperCase().replace('_',' ')}</strong><p>Expected HTTP {s.expected} · Actual {s.actual===null?'Not observed':s.actual}</p><p>{s.reason}</p><small>Mapped controls: {s.controls.join(', ')}</small></div>)}
   <details><summary>Canonical control context ({view.controls.length} mapped)</summary>{view.controls.map(c=><div className="control-detail" key={c.id}><strong>{c.id} — {c.name}</strong><p>{c.objective}</p><small>Enforcement: {c.enforcement_point}</small></div>)}</details>
   <p>Mappings include planned and unexecuted assertions. Current catalog labels are contextual. Control effectiveness not assessed; no compliance claim.</p>
  </>}
 </article>
}
