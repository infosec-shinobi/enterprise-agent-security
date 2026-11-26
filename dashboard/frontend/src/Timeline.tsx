import {useEffect,useState} from 'react';

const labels:Record<string,string>={accepted:'Execution accepted',manifest_validated:'Manifest validated',provisioning:'Provisioning infrastructure',services_ready:'Services ready',authenticated:'Agent authenticated',assertion:'Security assertion',runner_error:'Runner reported an error',cleanup_started:'Cleaning up disposable resources',cleanup_succeeded:'Cleanup succeeded',cleanup_failed:'Cleanup failed',evidence_saved:'Runner saved evidence',observation_gap:'Event collection incomplete',completed:'Execution completed'};
type Row={schema_version:1;operation_id:string;mode:string;sequence:number;observed_at:string;kind:string;scenario?:string;outcome?:string;expected?:number;actual?:number|null;recovery_required?:boolean};
export default function Timeline({runId}:{runId:string}){
 const [rows,setRows]=useState<Row[]>([]);
 const [status,setStatus]=useState('Connecting');
 useEffect(()=>{
  let cursor=0;
  const source=new EventSource('/api/v1/runs/'+encodeURIComponent(runId)+'/events');
  source.onopen=()=>setStatus('Connected');
  source.onerror=()=>setStatus('Disconnected — retrying; run status is independent');
  source.onmessage=e=>{
   try{
    const row=JSON.parse(e.data) as Row;
    if(row.schema_version!==1||row.operation_id!==runId||row.mode!=='autopilot'||!Number.isInteger(row.sequence)||String(row.sequence)!==e.lastEventId||!Object.prototype.hasOwnProperty.call(labels,row.kind))throw Error();
    if(row.sequence<=cursor)return;
    if(row.sequence!==cursor+1)throw Error();
    cursor=row.sequence;
    setRows(old=>[...old,row].slice(-132));
    if(row.kind==='completed'){source.close();setStatus('Complete')}
   }catch{source.close();setStatus('Invalid event stream — refresh page to replay')}
  };
  return ()=>source.close();
 },[runId]);
 return <article className="lab-card">
  <h2>Execution timeline</h2><p role="status">{status}</p>
  <p>Live observations only; validated evidence determines the final result.</p>
  <ol>{rows.map(row=><li key={row.sequence}>
   <small>{new Date(row.observed_at).toLocaleTimeString()} · #{row.sequence}</small>
   <p>{labels[row.kind]}{row.scenario?' — '+row.scenario:''}{row.outcome?' · '+row.outcome.toUpperCase():''}{row.expected!==undefined?' (expected '+row.expected+', actual '+(row.actual??'none')+')':''}{row.recovery_required?' · recovery required':''}</p>
  </li>)}</ol>
 </article>
}
