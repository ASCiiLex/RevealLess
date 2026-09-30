import { api } from './client'
import type { FeedPost } from './feed'

export interface PersonajeObra {
  id: number
  titulo: string
  slug: string
  imagen_url: string
}

export interface PersonajeDetalle {
  id: number
  nombre: string
  imagen_url: string
  nota: string | null
  obras: PersonajeObra[]
  suscripcion_id: number | null
  total_suscriptores: number
}

export function fetchPersonajeLanding(personajeId: number): Promise<PersonajeDetalle> {
  return api.get<PersonajeDetalle>(`/narrative/api/personajes/${personajeId}/`)
}

export function fetchFeedPersonaje(personajeId: number): Promise<FeedPost[]> {
  return api
    .get<{ results: FeedPost[] }>(`/narrative/api/feed/?personaje=${personajeId}`)
    .then((data) => data.results)
}