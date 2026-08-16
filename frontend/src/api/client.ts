import type { Asset, GraphPayload, Persona, PersonaDetail, ReviewItem } from '../types'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options })
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`)
  return response.json() as Promise<T>
}

export const api = {
  personas: () => request<Persona[]>('/api/personas'),
  persona: (id: string) => request<PersonaDetail>(`/api/personas/${id}`),
  assets: () => request<Asset[]>('/api/assets'),
  review: () => request<ReviewItem[]>('/api/review'),
  graph: (id: string) => request<GraphPayload>(`/api/graph/persona/${id}`),
  decide: (id: string, decision: string) => request(`/api/review/${id}/decision`, { method: 'POST', body: JSON.stringify({ decision }) }),
  resetDemo: () => request('/api/reset-demo', { method: 'POST' }),
  startImport: (path: string) => request<{ id: string }>('/api/import', { method: 'POST', body: JSON.stringify({ path }) }),
}
