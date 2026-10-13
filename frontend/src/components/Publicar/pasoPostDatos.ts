import { ApiError } from '../../api/client'
import type { DatosPost } from '../../api/publicar'
import { disposicionEfectiva } from '../Galeria/GaleriaPost'
import type { EstadoComparativa } from './Comparativa'
import type { ImagenBorrador } from './GaleriaEditor'
import type { PersonajeElegido } from './PersonajesEnfrentados'
import type { Seleccion } from './SelectorParteTema'

export const SIN_SELECCION: Seleccion = { id: null, label: null }
const ERROR_GENERICO = 'No se pudo publicar. Revisa los datos e inténtalo de nuevo.'

export function mensajeDeError(err: unknown): string {
  const cuerpo = err instanceof ApiError ? err.detail : null
  const detalle = (cuerpo as { detail?: unknown } | null)?.detail ?? cuerpo
  if (typeof detalle === 'string') return detalle
  if (detalle && typeof detalle === 'object') {
    const primero = Object.values(detalle)[0]
    if (Array.isArray(primero) && typeof primero[0] === 'string') return primero[0]
  }
  return ERROR_GENERICO
}

// Galería, segunda obra y personajes: se añaden a la petición solo si se usan.
export function datosExtra(
  imagenes: ImagenBorrador[],
  disposicion: string,
  comparativa: EstadoComparativa,
  parteOtra: Seleccion,
  personajes: PersonajeElegido[],
): Partial<DatosPost> {
  const extra: Partial<DatosPost> = {}
  if (imagenes.length === 1) {
    extra.image = imagenes[0].archivo
  } else if (imagenes.length > 1) {
    extra.imagenes = imagenes.map((i) => i.archivo)
    extra.etiquetas = imagenes.map((i) => i.etiqueta.trim())
    extra.enfoquesX = imagenes.map((i) => i.enfoqueX)
    extra.enfoquesY = imagenes.map((i) => i.enfoqueY)
    extra.zooms = imagenes.map((i) => i.zoom)
    extra.disposicion = disposicionEfectiva(imagenes.length, disposicion)
  }
  if (comparativa.activa) {
    if (comparativa.obra && parteOtra.id) {
      extra.obraCruzadaId = comparativa.obra.id
      extra.fronteraCruzadaId = parteOtra.id
      extra.modoCruce = comparativa.modo
    }
    if (personajes.length >= 2) {
      extra.personajesComparadosIds = personajes.filter((p) => p.id !== null).map((p) => p.id as number)
      extra.personajesPropuestos = personajes.filter((p) => p.id === null).map((p) => p.nombre)
    }
  }
  return extra
}