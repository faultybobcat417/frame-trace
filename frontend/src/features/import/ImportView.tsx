import { useState } from 'react'

const stages = ['DISCOVER','HASH','DECODE','SAMPLE','DETECT','EMBED','CLUSTER','PROJECT','COMPLETE']

export function ImportView({ onStart }: { onStart: (path: string) => Promise<void> }) {
  const [path,setPath] = useState('~/authorized-media')
  const [busy,setBusy] = useState(false)
  const [done,setDone] = useState(false)
  const run = async()=>{ setBusy(true); setDone(false); await onStart(path); setBusy(false); setDone(true) }
  return <section className="page">
    <header className="page-head"><div><span className="eyebrow">LOCAL IMPORT</span><h1>Media enters through explicit source boundaries.</h1><p>No social scraping. No hidden network calls. Folder and manifest adapters only.</p></div></header>
    <article className="import-panel"><div className="drop-zone"><span className="drop-icon">↳</span><h2>Authorized media package</h2><p>Folder path or package containing manifest.json + media/</p><input value={path} onChange={e=>setPath(e.target.value)} /><button className="primary" onClick={run} disabled={busy}>{busy ? 'PROCESSING…' : 'START IMPORT'}</button></div><div className="stage-list">{stages.map((s,i)=><div key={s} className={done ? 'done' : busy && i < 5 ? 'active' : ''}><i>{String(i+1).padStart(2,'0')}</i><span>{s}</span></div>)}</div></article>
  </section>
}
