import { useEffect, useState } from 'react'
import { api } from './api/client'
import { Shell, type View } from './components/Shell'
import { GraphView } from './features/graph/GraphView'
import { ImportView } from './features/import/ImportView'
import { MediaView } from './features/media/MediaView'
import { PersonaDetail } from './features/personas/PersonaDetail'
import { PersonaWall } from './features/personas/PersonaWall'
import { ReviewView } from './features/review/ReviewView'
import type { Asset, GraphPayload, Persona, PersonaDetail as PersonaDetailType, ReviewItem } from './types'
import './styles.css'

export default function App() {
  const [view,setView] = useState<View>('PERSONAS')
  const [personas,setPersonas] = useState<Persona[]>([])
  const [assets,setAssets] = useState<Asset[]>([])
  const [reviews,setReviews] = useState<ReviewItem[]>([])
  const [detail,setDetail] = useState<PersonaDetailType | null>(null)
  const [graph,setGraph] = useState<GraphPayload | undefined>()
  const [error,setError] = useState('')

  const refresh = async()=>{
    try {
      const [p,a,r] = await Promise.all([api.personas(),api.assets(),api.review()])
      setPersonas(p); setAssets(a); setReviews(r); setError('')
    } catch(e) { setError(e instanceof Error ? e.message : 'Unable to reach local API') }
  }

  useEffect(()=>{ refresh() },[])

  const openPersona = async(id:string)=>{ const d=await api.persona(id); setDetail(d) }
  const openGraph = async()=>{ if(!detail) return; setGraph(await api.graph(detail.id)); setView('GRAPH') }
  const decide = async(id:string,decision:string)=>{ await api.decide(id,decision); await refresh() }
  const startImport = async(path:string)=>{ await api.startImport(path) }

  let content
  if (view==='PERSONAS') content = detail ? <PersonaDetail detail={detail} onBack={()=>setDetail(null)} onGraph={openGraph}/> : <PersonaWall personas={personas} onOpen={openPersona}/>
  else if (view==='MEDIA') content = <MediaView assets={assets}/>
  else if (view==='REVIEW') content = <ReviewView items={reviews} onDecision={decide}/>
  else if (view==='IMPORT') content = <ImportView onStart={startImport}/>
  else content = <GraphView payload={graph} rootLabel={detail?.label ?? detail?.id}/>

  return <Shell view={view} setView={v=>{setView(v); if(v!=='PERSONAS') setDetail(detail)}}>{error && <div className="connection-error">API unavailable: {error}. Run <code>frame-trace demo</code> then <code>frame-trace serve</code>.</div>}{content}</Shell>
}
