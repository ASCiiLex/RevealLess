import { api } from './client'
import type { LomoObra } from '../components/Carousel/Lomo'

export interface TemaBusqueda {
  id: number
  nombre: string
  obra_id: number
  obra_titulo: string
  obra_slug: string
}

export interface ResultadoBusqueda {
  obras: LomoObra[]
  temas: TemaBusqueda[]
}

export function buscar(q: string): Promise<ResultadoBusqueda> {
  return api.get<ResultadoBusqueda>(`/narrative/api/buscar/?q=${encodeURIComponent(q)}`)
}