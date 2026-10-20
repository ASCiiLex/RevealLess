import { api } from './client'
import type { LomoObra } from '../components/Carousel/Lomo'

export interface CategoriaBusqueda {
  id: number
  nombre: string
  total_obras: number
}

export interface TemaBusqueda {
  id: number
  nombre: string
  obra_id: number
  obra_titulo: string
  obra_slug: string
  suscrito: boolean
  suscripcion_id: number | null
}

// Arco, temporada o saga ya empezado por el usuario.
export interface ArcoBusqueda {
  id: number
  nombre: string
  padre_nombre: string | null
  obra_id: number
  obra_titulo: string
  obra_slug: string
  suscrito: boolean
  suscripcion_id: number | null
}

export interface UsuarioBusqueda {
  username: string
  avatar_url: string
}

export interface HashtagBusqueda {
  name: string
}

export interface ResultadoBusqueda {
  obras: LomoObra[]
  arcos: ArcoBusqueda[]
  categorias: CategoriaBusqueda[]
  temas: TemaBusqueda[]
  usuarios: UsuarioBusqueda[]
  hashtags: HashtagBusqueda[]
}

export function buscar(q: string): Promise<ResultadoBusqueda> {
  return api.get<ResultadoBusqueda>(`/narrative/api/buscar/?q=${encodeURIComponent(q)}`)
}

// Cabecera del feed filtrado por arco; 404 si aún no se ha empezado.
export function fetchArco(unidadId: number): Promise<ArcoBusqueda> {
  return api.get<ArcoBusqueda>(`/narrative/api/arcos/${unidadId}/`)
}