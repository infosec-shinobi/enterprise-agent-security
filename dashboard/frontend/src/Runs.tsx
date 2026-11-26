import {useEffect,useState} from 'react';
import Timeline from './Timeline';
import Results from './Results';
import Manual from './Manual';
import {getRuns,startRun,type RunSnapshot} from './api';

export default function Runs(){
 const [snapshot,setSnapshot]=useState<RunSnapshot|null>(null);
 const [error,setError]=useState('');
 const [starting,setStarting]=useState(false);
 const [attempt,setAttempt]=useState(0);
 useEffect(()=>{
  let active=true;let timer:number|undefined;let controller:AbortController;
  async function poll(){
   controller=new AbortController();
   const timeout=window.setTimeout(()=>controller.abort(),4000);
   try{const v=await getRuns(controller.signal);if(active){setSnapshot(v);setError('')}}
   catch{if(active){setSnapshot(null);setError('Run status unavailable; refresh before starting again.')}}
   finally{window.clearTimeout(timeout);if(active)timer=window.setTimeout(poll,2000)}
  }
  void poll();
  return ()=>{active=false;controller?.abort();window.clearTimeout(timer)};
 },[attempt]);
 async function start(){
  if(starting||!snapshot||snapshot.blocked)return;
  if(!window.confirm('Start disposable Lab 01? Ensure ports 8000, 8001 and 8081 are free and no other lab is executing.'))return;
  setStarting(true);setError('');
  const controller=new AbortController();const timer=window.setTimeout(()=>controller.abort(),5000);
  try{await startRun('lab-01',controller.signal)}
  catch{setError('Start not confirmed. Check current status before retrying.')}
  finally{window.clearTimeout(timer);setSnapshot(null);setStarting(false);setAttempt(a=>a+1)}
 }
 const latest=snapshot?.latest;
 return <section>
  <div className="lab-heading"><h2>Automated lab execution</h2><button onClick={()=>setAttempt(a=>a+1)}>Refresh status</button></div>
  <article className="lab-card">
   <small>LAB-01 · AUTOPILOT</small><h2>Registry, identity, authorization and suspension</h2>
   <p>Runs the existing five security assertions in a disposable Compose project. Stop conflicting lab services first. Do not run CLI or manual Compose concurrently.</p>
   <button disabled={starting||!snapshot||snapshot.blocked||!snapshot.supported_labs.includes('lab-01')} onClick={()=>void start()}>{starting?'Submitting…':'Run Lab 01'}</button>
   {snapshot?.blocked&&<p role="status">Execution locked: active run or manual recovery required.</p>}
   {snapshot?.blocked&&!latest&&<p>Previous execution state unknown. Inspect data/dashboard-run.lock before recovery.</p>}
  </article>
  {error&&<p role="alert">{error}</p>}
  {!snapshot&&!error&&<p role="status">Checking run status…</p>}
  {latest&&<article className="lab-card">
   <small>LATEST RUN</small><h2 className={latest.status==='pass'?'service-available':latest.status==='running'?'':'service-unavailable'}>{latest.status.toUpperCase()}</h2>
   <p>{latest.reason}</p><p>Run ID: {latest.run_id}</p><p>Project: {latest.project}</p>
   <p>Started: {new Date(latest.started_at).toLocaleString()}</p>
   {latest.finished_at&&<p>Finished: {new Date(latest.finished_at).toLocaleString()}</p>}
   {latest.exit_code!==null&&<p>Exit code: {latest.exit_code}</p>}
   {latest.evidence_path&&<p>Evidence: {latest.evidence_path}</p>}
   {latest.recovery_required&&<p role="alert">Manual recovery required. Do not remove the lock until runner termination and scoped cleanup are verified.</p>}
   {latest.status==='error'&&<p>Execution error is not a failed security assertion.</p>}
  </article>}
  {latest&&latest.status!=='running'&&latest.evidence_path&&<Results key={latest.run_id} runId={latest.run_id}/>}
  <Manual labId="lab-01"/>
  {latest&&<Timeline key={latest.run_id} runId={latest.run_id}/>}
 </section>
}
