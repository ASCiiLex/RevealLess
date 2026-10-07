import { api } from './client'

export type NivelSuscripcion = 'obra' | 'unidad' | 'tema' | 'personaje'

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

export interface SuscripcionPersonaje {
  id: number
  nombre: string
  imagen_url: string
}

export interface Suscripcion {
  id: number
  obra: SuscripcionObra | null // null en suscripciones a personaje
  unidad: SuscripcionUnidad | null
  tema: SuscripcionTema | null
  personaje: SuscripcionPersonaje | null
  nivel: NivelSuscripcion
  activa: boolean
  no_leidos: number
  ultima_visita: string | null
}

export interface ObraRelacionada {
  id: number
  slug: string
  titulo: string
}

export interface ObraDetalle {
  obra: { id: number; titulo: string; slug: string }
  unidades: { id: number; etiqueta: string; orden_inicio: number; orden_fin: number }[]
  temas: { id: number; nombre: string }[]
  obras_relacionadas: ObraRelacionada[]
}

export type EstadoSolicitud = 'pendiente' | 'aprobada' | 'rechazada'

export interface SolicitudTema {
  id: number
  obra: number
  obra_titulo: string
  nombre: string
  estado: EstadoSolicitud
  creado_en: string
  resuelto_en: string | null
}

// Resultado del buscador de partes: el detalle (temporada, saga…) distingue nombres repetidos.
export interface UnidadBuscada {
  id: number
  label: string
  detalle: string | null
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

export function crearSuscripcionPersonaje(personajeId: number): Promise<Suscripcion> {
  return api.post<Suscripcion>('/api/suscripciones/', { personaje: personajeId })
}

export function eliminarSuscripcion(id: number): Promise<void> {
  return api.delete<void>(`/api/suscripciones/${id}/`)
}

export function toggleActivaSuscripcion(id: number, activa: boolean): Promise<Suscripcion> {
  return api.patch<Suscripcion>(`/api/suscripciones/${id}/activa/`, { activa })
}

export function crearSolicitudTema(obraId: number, nombre: string): Promise<SolicitudTema> {
  return api.post<SolicitudTema>('/narrative/api/solicitudes-tema/', {
    obra: obraId,
    nombre,
  })
}

export function buscarUnidades(obraSlug: string, q: string): Promise<UnidadBuscada[]> {
  const params = q ? `?q=${encodeURIComponent(q)}` : ''
  return api
    .get<{ unidades: { id: number; etiqueta: string; padre_etiqueta: string | null }[] }>(
      `/narrative/api/obras/${obraSlug}/unidades/${params}`
    )
    .then((data) => data.unidades.map((u) => ({ id: u.id, label: u.etiqueta, detalle: u.padre_etiqueta })))
}

export interface ObraContextoPublicar {
  obra: { id: number; titulo: string; slug: string }
  temas: { id: number; nombre: string }[]
}

export function fetchObraContextoPublicar(obraSlug: string): Promise<ObraContextoPublicar> {
  return api.get<ObraContextoPublicar>(`/narrative/api/obras/${obraSlug}/contexto-publicar/`)
}