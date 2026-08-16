import type { PersonaDetail as PersonaDetailType } from '../../types'

function cropUrl(path?: string | null) { return path ? '/' + path.replace(/^demo\//, 'demo-') : '' }

export function PersonaDetail({ detail, onBack, onGraph }: { detail: PersonaDetailType; onBack: () => void; onGraph: () => void }) {
  const total = detail.sources.reduce((sum, s) => sum + s.appearance_count, 0) || 1
  return <section className="page detail-page">
    <button className="text-button" onClick={onBack}>← PERSONAS</button>
    <header className="detail-head"><img src={cropUrl(detail.representative_crop)} alt="persona"/><div><span className="eyebrow">{detail.id}</span><h1>{detail.label || detail.id}</h1><p>Anonymous recurring persona inside the authorized demo corpus.</p><div className="stat-row"><span><b>{detail.appearance_count}</b> appearances</span><span><b>{detail.source_count}</b> sources</span><span><b>{detail.neighbors.length}</b> co-occurring personas</span></div></div><button className="primary" onClick={onGraph}>OPEN GRAPH →</button></header>
    <div className="detail-grid">
      <article className="panel span-2"><div className="panel-title"><span>TIMELINE</span><small>{detail.first_seen?.slice(0,10)} → {detail.last_seen?.slice(0,10)}</small></div><div className="timeline">{detail.appearances.slice().reverse().map((a,i)=><div key={a.id} className="tick" style={{left:`${(i/(Math.max(1,detail.appearances.length-1)))*100}%`}} title={a.captured_at ?? ''}/>)}</div></article>
      <article className="panel"><div className="panel-title"><span>SOURCE DISTRIBUTION</span></div><div className="bars">{detail.sources.map(s => <div key={s.id}><div className="bar-label"><span>{s.name}</span><b>{s.appearance_count}</b></div><div className="bar"><i style={{width:`${(s.appearance_count/total)*100}%`}}/></div></div>)}</div></article>
      <article className="panel"><div className="panel-title"><span>CO-OCCURRENCES</span><small>observed media overlap only</small></div><div className="neighbor-list">{detail.neighbors.map(n=><div key={n.id}><span>{n.id} · {n.label}</span><b>{n.shared_asset_count} shared</b></div>)}</div></article>
      <article className="panel span-2"><div className="panel-title"><span>APPEARANCE GRID</span><small>provenance preserved to asset + source</small></div><div className="appearance-grid">{detail.appearances.map(a=><div className="appearance" key={a.id}><img src={cropUrl(a.crop_path)} alt="appearance"/><div><strong>{a.source_name}</strong><span>{a.filename}</span><small>{a.captured_at?.slice(0,10) ?? 'undated'}</small></div></div>)}</div></article>
    </div>
  </section>
}
