export type Health = {status:'ok';service:'playground-api';api_version:'v1'};
export async function getHealth(signal: AbortSignal): Promise<Health> {
  const response = await fetch('/api/v1/health', {signal, cache:'no-store'});
  if (!response.ok) throw new Error('API unavailable');
  const data: unknown = await response.json();
  if (!data || typeof data !== 'object' || !('status' in data) || data.status !== 'ok' || !('service' in data) || data.service !== 'playground-api' || !('api_version' in data) || data.api_version !== 'v1') throw new Error('Unexpected API response');
  return {status:'ok',service:'playground-api',api_version:'v1'};
}

export type Control = {id:string;name:string;objective:string;enforcement_point:string};
export type Scenario = {id:string;title:string;controls:string[];action:string;expected:{http_status:number}};
export type Lab = {id:string;title:string;description:string;schema_version:1;manual_path:string;services:string[];scenarios:Scenario[];controls:Control[]};
export type Catalog = {labs:Lab[];issues:{directory:string;reason:string}[]};
type Obj = Record<string,unknown>;
const obj=(v:unknown):v is Obj=>typeof v==='object'&&v!==null&&!Array.isArray(v);
const strings=(v:unknown):v is string[]=>Array.isArray(v)&&v.every(x=>typeof x==='string');
const fields=(v:Obj,keys:string[])=>keys.every(k=>typeof v[k]==='string');
const control=(v:unknown):v is Control=>obj(v)&&fields(v,['id','name','objective','enforcement_point']);
const scenario=(v:unknown):v is Scenario=>obj(v)&&fields(v,['id','title','action'])&&strings(v.controls)&&obj(v.expected)&&typeof v.expected.http_status==='number'&&Number.isInteger(v.expected.http_status)&&v.expected.http_status>=100&&v.expected.http_status<=599;
const lab=(v:unknown):v is Lab=>obj(v)&&fields(v,['id','title','description','manual_path'])&&v.schema_version===1&&strings(v.services)&&Array.isArray(v.scenarios)&&v.scenarios.every(scenario)&&Array.isArray(v.controls)&&v.controls.every(control);
export async function getLabs(signal:AbortSignal):Promise<Catalog>{
 const response=await fetch('/api/v1/labs',{signal,cache:'no-store'});
 if(!response.ok)throw new Error('Catalog unavailable');
 const v:unknown=await response.json();
 if(!obj(v)||!Array.isArray(v.labs)||!v.labs.every(lab)||!Array.isArray(v.issues)||!v.issues.every(i=>obj(i)&&fields(i,['directory','reason'])))throw new Error('Invalid catalog response');
 return {labs:v.labs,issues:v.issues};
}

export type ServiceObservation={id:string;name:string;role:string;endpoint:string|null;status:'available'|'unavailable'|'unknown';reason:string;checked_at:string;duration_ms:number|null;http_status:number|null;control_effectiveness:'not_assessed'};
const nullableInt=(v:unknown)=>v===null||(typeof v==='number'&&Number.isInteger(v)&&v>=0);
const observation=(v:unknown):v is ServiceObservation=>obj(v)&&fields(v,['id','name','role','reason','checked_at'])&&(v.endpoint===null||typeof v.endpoint==='string')&&(v.status==='available'||v.status==='unavailable'||v.status==='unknown')&&nullableInt(v.duration_ms)&&nullableInt(v.http_status)&&v.control_effectiveness==='not_assessed'&&typeof v.checked_at==='string'&&Number.isFinite(Date.parse(v.checked_at));
export async function getServices(signal:AbortSignal):Promise<ServiceObservation[]>{
 let response=await fetch('/api/v1/services',{signal,cache:'no-store'});
 // A prior request can still be finishing after React development remount.
 if(response.status===429){
  await new Promise<void>(resolve=>window.setTimeout(resolve,3200));
  signal.throwIfAborted();
  response=await fetch('/api/v1/services',{signal,cache:'no-store'});
 }
 if(!response.ok)throw new Error('Service observations unavailable');
 const v:unknown=await response.json();
 if(!obj(v)||!Array.isArray(v.services)||!v.services.every(observation))throw new Error('Invalid service response');
 return v.services;
}

export type Run={run_id:string;lab_id:string;project:string;status:'running'|'pass'|'fail'|'error';started_at:string;finished_at:string|null;exit_code:number|null;evidence_path:string|null;reason:string;recovery_required:boolean};
export type RunSnapshot={supported_labs:string[];blocked:boolean;latest:Run|null};
const nullableString=(v:unknown)=>v===null||typeof v==='string';
const run=(v:unknown):v is Run=>obj(v)&&fields(v,['run_id','lab_id','project','started_at','reason'])&&(v.status==='running'||v.status==='pass'||v.status==='fail'||v.status==='error')&&nullableString(v.finished_at)&&nullableString(v.evidence_path)&&(v.exit_code===null||typeof v.exit_code==='number')&&typeof v.recovery_required==='boolean';
export async function getRuns(signal:AbortSignal):Promise<RunSnapshot>{
 const r=await fetch('/api/v1/runs',{signal,cache:'no-store'});
 if(!r.ok)throw new Error('Run status unavailable');
 const v:unknown=await r.json();
 if(!obj(v)||!strings(v.supported_labs)||typeof v.blocked!=='boolean'||!(v.latest===null||run(v.latest)))throw new Error('Invalid run status');
 return {supported_labs:v.supported_labs,blocked:v.blocked,latest:v.latest};
}
export async function startRun(lab_id:string,signal:AbortSignal):Promise<Run>{
 const r=await fetch('/api/v1/runs',{method:'POST',headers:{'Content-Type':'application/json','X-EAS-Action':'start-run'},body:JSON.stringify({lab_id}),signal});
 if(r.status===409)throw new Error('Run active or recovery required');
 if(r.status!==202)throw new Error('Start request rejected or unavailable');
 const v:unknown=await r.json();
 if(!run(v))throw new Error('Invalid start response');
 return v;
}
