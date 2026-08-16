import { useMemo } from 'react'
import { Background, Controls, Handle, MiniMap, Position, ReactFlow, type Edge, type Node, type NodeProps } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { GraphPayload } from '../../types'

function EntityNode({ data }: NodeProps) {
  const d = data as { label?: string; type?: string }
  return <div className={`graph-node ${d.type ?? ''}`}><Handle type="target" position={Position.Left}/><span>{(d.type ?? 'node').toUpperCase()}</span><strong>{d.label}</strong><Handle type="source" position={Position.Right}/></div>
}

const nodeTypes = { entity: EntityNode }

export function GraphView({ payload, rootLabel }: { payload?: GraphPayload; rootLabel?: string }) {
  const nodes = useMemo<Node[]>(()=> (payload?.nodes ?? []).map((node,index)=>({id:node.id,type:'entity',position:{x:(index%4)*280,y:Math.floor(index/4)*170},data:{label:node.label,type:node.type}})),[payload])
  const edges = useMemo<Edge[]>(()=> (payload?.edges ?? []).map(edge=>({id:edge.id,source:edge.source,target:edge.target,label:edge.type.replaceAll('_',' '),animated:edge.type==='co_occurs_with'})),[payload])
  return <section className="graph-page"><header className="graph-head"><div><span className="eyebrow">RELATIONSHIP GRAPH</span><h1>{rootLabel ? `Network around ${rootLabel}` : 'Select a persona to project its local graph.'}</h1><p>Edges mean observed media evidence only — never inferred friendship or affiliation.</p></div><div className="legend"><span><i className="dot persona"/>Persona</span><span><i className="dot source"/>Source</span><span><i className="dot asset"/>Asset</span></div></header><div className="flow-wrap">{nodes.length ? <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView proOptions={{hideAttribution:true}}><Background gap={24} size={1}/><Controls/><MiniMap pannable zoomable/></ReactFlow> : <div className="empty graph-empty">Open a persona, then choose <b>OPEN GRAPH</b>.</div>}</div></section>
}
