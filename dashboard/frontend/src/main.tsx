import {StrictMode,useEffect,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {getHealth} from './api';
import './style.css';

const pages = [
 ['Overview','B01','Application status and development milestones.'],
 ['Labs','B02','Discover available labs and their manual instructions.'],
 ['Services','B03','Inspect actual service availability.'],
 ['Runs','B04–B06','Execute labs and inspect real results.'],
 ['Sandbox','C01–C07','Explore controlled security experiments.'],
 ['Controls','F01–F02','Review canonical controls and supporting evidence.'],
 ['Frameworks','G01–G06','Explore versioned mappings to external frameworks.'],
 ['Evidence','F03','Review and export historical evidence.']
] as const;
type Page = typeof pages[number][0];
function App(){
 const [page,setPage]=useState<Page>('Overview');
 const [dark,setDark]=useState(()=>{try{return localStorage.getItem('eas-theme')!=='light'}catch{return true}});
 const [status,setStatus]=useState<'checking'|'connected'|'unavailable'>('checking');
 const [attempt,setAttempt]=useState(0);
 useEffect(()=>{document.documentElement.dataset.theme=dark?'dark':'light';try{localStorage.setItem('eas-theme',dark?'dark':'light')}catch{}},[dark]);
 useEffect(()=>{
  const controller=new AbortController();
  let active=true;
  setStatus('checking');
  const timer=window.setTimeout(()=>controller.abort(),4000);
  getHealth(controller.signal).then(()=>{if(active)setStatus('connected')}).catch(()=>{if(active)setStatus('unavailable')}).finally(()=>window.clearTimeout(timer));
  return ()=>{active=false;window.clearTimeout(timer);controller.abort()};
 },[attempt]);
 const selected=pages.find(p=>p[0]===page)!;
 return <div className="shell">
  <aside><div className="brand"><span className="mark">EAS</span><div>Enterprise Agent<br/>Security</div></div><small>PLAYGROUND / LOCAL</small><nav aria-label="Main navigation">{pages.map(p=><button key={p[0]} aria-current={page===p[0]?'page':undefined} onClick={()=>setPage(p[0])}>{p[0]}</button>)}</nav><div className="foot">Development build · B01</div></aside>
  <main><header><span>Workspace / {page}</span><button onClick={()=>setDark(!dark)}>{dark?'Light mode':'Dark mode'}</button></header>
  <section className="intro"><small>SECURITY ENGINEERING WORKSPACE</small><h1>{page==='Overview'?'Agent Security Playground':page}</h1><p>{selected[2]}</p></section>
  <div className="status"><div><small>PLAYGROUND API</small><strong role="status" className={status}>{status==='connected'?'Connected':status==='checking'?'Checking…':'Unavailable'}</strong><p>API connectivity only; lab services are not checked.</p></div><button onClick={()=>setAttempt(a=>a+1)}>Refresh</button></div>
  {page==='Overview'?<><h2>Explore the workspace</h2><div className="cards">{pages.slice(1).map(p=><button className="tile" key={p[0]} onClick={()=>setPage(p[0])}><small>{p[1]} · PLANNED</small><h3>{p[0]}</h3><p>{p[2]}</p><span>Explore →</span></button>)}</div></>:<section className="placeholder"><small>{selected[1]} · PLANNED</small><h2>{page==='Frameworks'?'Canonical controls, multiple frameworks':'Not implemented yet'}</h2><p>{page==='Frameworks'?'Native controls will remain the source of truth. Versioned external mappings will link framework outcomes to controls and evidence. No mappings or compliance results are loaded in B01.':'This workspace is reserved for a later roadmap task. No live results are available here yet.'}</p><button onClick={()=>setPage('Overview')}>Back to overview</button></section>}
  </main></div>
}
createRoot(document.getElementById('root')!).render(<StrictMode><App/></StrictMode>);
