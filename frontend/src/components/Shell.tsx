import type { ReactNode } from 'react'

export type View = 'PERSONAS' | 'MEDIA' | 'GRAPH' | 'REVIEW' | 'IMPORT'

export function Shell({ view, setView, children }: { view: View; setView: (view: View) => void; children: ReactNode }) {
  const nav: View[] = ['PERSONAS', 'MEDIA', 'GRAPH', 'REVIEW', 'IMPORT']
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">FT</span><div><strong>FRAME TRACE</strong><small>LOCAL VISUAL GRAPH</small></div></div>
      <nav>{nav.map(item => <button key={item} className={view === item ? 'active' : ''} onClick={() => setView(item)}>{item}</button>)}</nav>
      <div className="boundary"><span>AUTHORIZED CORPUS</span><strong>Anonymous entities only</strong><small>No web identity lookup · no surveillance feeds</small></div>
    </aside>
    <main>{children}</main>
  </div>
}
