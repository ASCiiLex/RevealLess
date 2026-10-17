import { api } from './client'

interface UnidadPost {
  id: number
  nombre: string
  tipo: string
  etiqueta: string
  orden_inicio: number
  orden_fin: number
  padre?: number | null
  padre_etiqueta?: string | null
}

export interface ImagenPost {
  url: string
  etiqueta: string
  // Encuadre en %: punto de enfoque y zoom (100 = sin zoom).
  enfoque_x?: number
  enfoque_y?: number
  zoom?: number
}

export interface PersonajeComparado {
  // null mientras es una propuesta pendiente de revisión.
  id: number | null
  nombre: string
  imagen_url: string | null
  pendiente?: boolean
}

export interface TemaPost {
  id: number
  nombre: string
}

export interface FeedPost {
  id: number
  autor: string
  autor_avatar: string
  obra_titulo: string
  obra_slug: string
  // Opcionales: otras vistas pueden serializar posts sin estos campos.
  obra_cruzada?: { titulo: string; slug: string } | null
  modo_cruce?: 'comparativa' | 'misma_escena'
  temas?: TemaPost[]
  text: string
  imagen: string | null
  imagenes?: ImagenPost[]
  disposicion?: string
  personajes_comparados?: PersonajeComparado[]
  referencia_narrativa: (UnidadPost & { padre: number | null; padre_etiqueta: string | null }) | null
  frontera_spoiler: UnidadPost | null
  frontera_cruzada?: UnidadPost | null
  nivel_spoiler: string
  emocion_autor: string | null
  created_at: string
  likes_count: number
  comments_count: number
  // Totales por emoción ya calculados: la tarjeta no necesita pedirlos.
  reacciones_totales?: Record<string, number>
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