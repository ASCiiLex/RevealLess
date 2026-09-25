import { api } from './client'

export interface TemaLandingObra {
  id: number
  titulo: string
  slug: string
  tema_id: number
}

export interface TemaLanding {
  id: number
  nombre: string
  obra_slug: string
  obras: TemaLandingObra[]
  suscrito: boolean
  suscripcion_id: number | null
  total_suscriptores: number
}

export function fetchTemaLanding(temaId: number): Promise<TemaLanding> {
  return api.get<TemaLanding>(`/narrative/api/temas/${temaId}/`)
}