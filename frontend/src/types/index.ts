export type Persona = {
  id: string
  label?: string | null
  status: string
  appearance_count: number
  source_count: number
  first_seen?: string | null
  last_seen?: string | null
  representative_crop?: string | null
}

export type Appearance = {
  id: string
  persona_id: string
  asset_id: string
  filename: string
  kind: string
  captured_at?: string | null
  source_id: string
  source_name: string
  crop_path?: string | null
}

export type Neighbor = {
  id: string
  label?: string | null
  shared_asset_count: number
}

export type PersonaDetail = Persona & {
  appearances: Appearance[]
  neighbors: Neighbor[]
  sources: { id: string; name: string; appearance_count: number }[]
}

export type Asset = {
  id: string
  source_id: string
  source_name: string
  filename: string
  kind: string
  captured_at?: string | null
  persona_count: number
  persona_ids?: string | null
}

export type ReviewItem = {
  detection_id: string
  candidate_persona_id?: string | null
  candidate_label?: string | null
  similarity?: number | null
  crop_path?: string | null
  asset_id: string
  filename: string
  source_name: string
}

export type GraphPayload = {
  nodes: { id: string; type: string; label: string; data: Record<string, unknown> }[]
  edges: { id: string; source: string; target: string; type: string; data: Record<string, unknown> }[]
}
