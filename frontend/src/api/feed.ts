import { api } from './client'

export interface FeedPost {
  id: number
  autor: string
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
}

interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export function fetchFeed(): Promise<PaginatedResponse<FeedPost>> {
  return api.get<PaginatedResponse<FeedPost>>('/narrative/api/feed/')
}