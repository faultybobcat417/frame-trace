import { useMemo, useState } from 'react'
import type { Persona } from '../../types'

function cropUrl(path?: string | null) {
  if (!path) return ''
  return '/' + path.replace(/^demo\//, 'demo-')
}

export function PersonaWall({ personas, onOpen }: { personas: Persona[]; onOpen: (id: string) => void }) {
  const [query, setQuery] = useState('')
  const filtered = useMemo(() => personas.filter(p => `${p.id} ${p.label ?? ''}`.toLowerCase().includes(query.toLowerCase())), [personas, query])
  return <section className="page">
    <header className="page-head"><div><span className="eyebrow">PERSONA INDEX</span><h1>Recurring people, without identity lookup.</h1><p>Anonymous clusters inside the media you explicitly imported.</p></div><div className="metric-block"><strong>{personas.length}</strong><span>personas</span></div></header>
    <div className="toolbar"><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search persona ID or local label"/><span>{filtered.reduce((n,p)=>n+p.appearance_count,0)} appearances</span></div>
    <div className="persona-grid">{filtered.map(p => <button className="persona-card" key={p.id} onClick={() => onOpen(p.id)}>
      <div className="portrait-wrap"><img src={cropUrl(p.representative_crop)} alt="synthetic persona fixture"/><span className={`status ${p.status}`}>{p.status.replace('_',' ')}</span></div>
      <div className="persona-card-body"><div className="id-row"><strong>{p.id}</strong><span>{p.label}</span></div><div className="counts"><span><b>{p.appearance_count}</b> appearances</span><span><b>{p.source_count}</b> sources</span></div><small>{p.first_seen ? new Date(p.first_seen).toLocaleDateString() : '—'} → {p.last_seen ? new Date(p.last_seen).toLocaleDateString() : '—'}</small></div>
    </button>)}</div>
  </section>
}
