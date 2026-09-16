import { api } from './client'

export interface FeedPost {
  id: number
  autor: string
  autor_avatar: string
  obra_titulo: string
  obra_slug: string
  text: string
  imagen: string | null
  referencia_narrativa: {
    id: number
    nombre: string
    tipo: string
    etiqueta: string
    orden_inicio: number
    orden_fin: number
    padre: number | null
    padre_etiqueta: string | null
  } | null
  frontera_spoiler: {
    id: number
    nombre: string
    tipo: string
    etiqueta: string
    orden_inicio: number
    orden_fin: number
  } | null
  nivel_spoiler: string
  emocion_autor: string | null
  created_at: string
  likes_count: number
  comments_count: number
  user_reaction: string | null
  is_own_post: boolean
}

interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export function fetchFeed(obraId?: number | null, hashtag?: string): Promise<PaginatedResponse<FeedPost>> {
  const params = new URLSearchParams()
  if (obraId) params.set('obra', String(obraId))
  if (hashtag) params.set('hashtag', hashtag)
  const query = params.toString()
  return api.get<PaginatedResponse<FeedPost>>(
    `/narrative/api/feed/${query ? `?${query}` : ''}`
  )
}