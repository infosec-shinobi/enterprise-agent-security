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
