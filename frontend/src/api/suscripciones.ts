import { api } from './client'

export type NivelSuscripcion = 'obra' | 'unidad' | 'tema'

export interface SuscripcionObra {
  id: number
  titulo: string
  slug: string
  imagen_url: string
}

export interface SuscripcionUnidad {
  id: number
  etiqueta: string
}

export interface SuscripcionTema {
  id: number
  nombre: string
}

export interface Suscripcion {
  id: number
  obra: SuscripcionObra
  unidad: SuscripcionUnidad | null
  tema: SuscripcionTema | null
  nivel: NivelSuscripcion
  no_leidos: number
  ultima_visita: string | null
}

export interface ObraDetalle {
  obra: { id: number; titulo: string; slug: string }
  unidades: { id: number; etiqueta: string }[]
  temas: { id: number; nombre: string }[]
}

export function fetchSuscripciones(): Promise<Suscripcion[]> {
  return api.get<Suscripcion[]>('/api/suscripciones/')
}

export function fetchObraDetalle(obraSlug: string): Promise<ObraDetalle> {
  return api.get<ObraDetalle>(`/narrative/api/obras/${obraSlug}/detalle/`)
}

export function crearSuscripcion(
  obraSlug: string,
  opciones: { unidadId?: number; temaId?: number } = {}
): Promise<Suscripcion> {
  return api.post<Suscripcion>('/api/suscripciones/', {
    obra: obraSlug,
    unidad: opciones.unidadId ?? null,
    tema: opciones.temaId ?? null,
  })
}

export function eliminarSuscripcion(id: number): Promise<void> {
  return api.delete<void>(`/api/suscripciones/${id}/`)
}