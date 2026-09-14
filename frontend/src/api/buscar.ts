import { api } from './client'
import type { LomoObra } from '../components/Carousel/Lomo'

export interface TemaBusqueda {
  id: number
  nombre: string
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

export interface PostBusqueda {
  id: number
  text: string
  image: string
}

export interface ResultadoBusqueda {
  obras: LomoObra[]
  temas: TemaBusqueda[]
  usuarios: UsuarioBusqueda[]
  hashtags: HashtagBusqueda[]
  posts: PostBusqueda[]
}

export function buscar(q: string): Promise<ResultadoBusqueda> {
  return api.get<ResultadoBusqueda>(`/narrative/api/buscar/?q=${encodeURIComponent(q)}`)
}