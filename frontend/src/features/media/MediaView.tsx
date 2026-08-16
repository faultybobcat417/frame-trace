import type { Asset } from '../../types'

export function MediaView({ assets }: { assets: Asset[] }) {
  return <section className="page">
    <header className="page-head"><div><span className="eyebrow">MEDIA LEDGER</span><h1>Every graph edge remains tied to source media.</h1><p>Assets are local, hashed, and grouped by imported source.</p></div><div className="metric-block"><strong>{assets.length}</strong><span>assets</span></div></header>
    <div className="media-table"><div className="media-row head"><span>ASSET</span><span>SOURCE</span><span>TYPE</span><span>PERSONAS</span><span>DATE</span></div>{assets.map(a=><div className="media-row" key={a.id}><span><b>{a.id}</b><small>{a.filename}</small></span><span>{a.source_name}</span><span className="chip">{a.kind}</span><span>{a.persona_count}</span><span>{a.captured_at?.slice(0,10) ?? '—'}</span></div>)}</div>
  </section>
}
