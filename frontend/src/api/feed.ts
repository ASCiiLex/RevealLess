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
  is_saved: boolean
}

interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface FetchFeedOptions {
  obraId?: number | null
  hashtag?: string
  temaId?: number
}

export function fetchFeed(opciones: FetchFeedOptions = {}): Promise<PaginatedResponse<FeedPost>> {
  const params = new URLSearchParams()
  if (opciones.obraId) params.set('obra', String(opciones.obraId))
  if (opciones.hashtag) params.set('hashtag', opciones.hashtag)
  if (opciones.temaId) params.set('tema', String(opciones.temaId))
  const query = params.toString()
  return api.get<PaginatedResponse<FeedPost>>(
    `/narrative/api/feed/${query ? `?${query}` : ''}`
  )
}