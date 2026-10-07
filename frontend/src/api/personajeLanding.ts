import { api } from './client'
import type { FeedPost } from './feed'

export interface PersonajeObra {
  id: number
  titulo: string
  slug: string
  imagen_url: string
}

// Obra desde la que se abrió la landing: nombre, imagen y nota se calculan solo con ella.
export interface PersonajeContexto {
  titulo: string
  slug: string
}

// Identidad vinculada (Sogeking ↔ Usopp): solo llega si el lector ya conoce el vínculo.
export interface IdentidadVinculada {
  id: number
  nombre: string
}

export interface PersonajeDetalle {
  id: number
  nombre: string
  imagen_url: string
  nota: string | null
  contexto: PersonajeContexto | null
  identidad_de: IdentidadVinculada | null
  otras_identidades: IdentidadVinculada[]
  obras: PersonajeObra[]
  suscripcion_id: number | null
  total_suscriptores: number
}

export function fetchPersonajeLanding(personajeId: number, obraSlug?: string | null): Promise<PersonajeDetalle> {
  const query = obraSlug ? `?obra=${encodeURIComponent(obraSlug)}` : ''
  return api.get<PersonajeDetalle>(`/narrative/api/personajes/${personajeId}/${query}`)
}

export function fetchFeedPersonaje(personajeId: number): Promise<FeedPost[]> {
  return api
    .get<{ results: FeedPost[] }>(`/narrative/api/feed/?personaje=${personajeId}`)
    .then((data) => data.results)
}