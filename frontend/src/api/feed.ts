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
  } | null
  nivel_spoiler: string
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

export function fetchFeed(obraId?: number | null): Promise<PaginatedResponse<FeedPost>> {
  const url = obraId
    ? `/narrative/api/feed/?obra=${obraId}`
    : '/narrative/api/feed/'
  return api.get<PaginatedResponse<FeedPost>>(url)
}