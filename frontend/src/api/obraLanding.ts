import { api } from './client'

export interface TemaLanding {
  id: number
  nombre: string
  suscrito: boolean
  suscripcion_id: number | null
}

export interface CategoriaRef {
  id: number
  nombre: string
}

export interface ObraRelacionada {
  id: number
  titulo: string
  slug: string
}

export interface PersonajeLanding {
  id: number
  nombre: string
  imagen_url: string
  nota: string | null
  nivel: number
  suscripcion_id: number | null
}

export interface NivelRelevancia {
  valor: number
  nombre: string
  por_defecto: boolean
}

export interface ObraLanding {
  id: number
  titulo: string
  slug: string
  sinopsis: string
  imagen_url: string
  categorias: string[]
  categorias_detalle: CategoriaRef[]
  suscrito: boolean
  suscripcion_id: number | null
  progreso_pct: number | null
  total_suscriptores: number
  temas: TemaLanding[]
  obras_relacionadas: ObraRelacionada[]
  personajes: PersonajeLanding[]
  niveles_relevancia: NivelRelevancia[]
}

export function fetchObraLanding(obraSlug: string): Promise<ObraLanding> {
  return api.get<ObraLanding>(`/narrative/api/obras/${obraSlug}/landing/`)
}