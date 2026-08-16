import type { ReviewItem } from '../../types'

function cropUrl(path?: string | null) { return path ? '/' + path.replace(/^demo\//, 'demo-') : '' }

export function ReviewView({ items, onDecision }: { items: ReviewItem[]; onDecision: (id: string, decision: string) => void }) {
  return <section className="page">
    <header className="page-head"><div><span className="eyebrow">HUMAN REVIEW</span><h1>Abstention is a feature.</h1><p>Weak assignments stop here instead of silently contaminating the graph.</p></div><div className="metric-block"><strong>{items.length}</strong><span>open items</span></div></header>
    <div className="review-stack">{items.length === 0 ? <div className="empty">Review queue clear.</div> : items.map(item => <article className="review-card" key={item.detection_id}><div className="review-crop"><img src={cropUrl(item.crop_path)} alt="candidate"/><span>{item.detection_id}</span></div><div className="review-copy"><span className="eyebrow">POTENTIAL MATCH</span><h2>{item.candidate_persona_id} · {item.candidate_label}</h2><p>{item.source_name} / {item.filename}</p><div className="similarity"><span>heuristic similarity</span><strong>{item.similarity?.toFixed(2) ?? '—'}</strong></div></div><div className="review-actions"><button className="primary" onClick={()=>onDecision(item.detection_id,'same')}>SAME PERSON</button><button onClick={()=>onDecision(item.detection_id,'different')}>DIFFERENT</button><button onClick={()=>onDecision(item.detection_id,'unknown')}>LEAVE UNKNOWN</button></div></article>)}</div>
  </section>
}
