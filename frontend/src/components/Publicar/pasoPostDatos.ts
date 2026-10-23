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

// Algún personaje elegido de la obra comparada: su primera aparición basta como frontera cruzada.
export function hayPersonajeDeOtraObra(personajes: PersonajeElegido[]): boolean {
  return personajes.some((p) => p.deOtraObra && p.id !== null)
}

// Comparativa sin parte de la otra obra (ni personaje suyo que la sustituya) o enfrentamiento de uno solo.
export function comparativaIncompleta(
  comparativa: EstadoComparativa,
  parteOtra: Seleccion,
  personajes: PersonajeElegido[],
): boolean {
  if (!comparativa.activa) return false
  const sinParteOtra = comparativa.obra !== null && !parteOtra.id && !hayPersonajeDeOtraObra(personajes)
  return sinParteOtra || personajes.length === 1
}

export function pistaParte(temaPropuesto: string | null, parteDeIA: boolean): string {
  if (temaPropuesto) return 'Si el tema ya existe en esta obra se asigna al publicar; si no, se revisará antes de crearlo.'
  if (parteDeIA) {
    return 'Parte propuesta por la IA: compruébala. Solo indica de qué habla; quién lo ve lo decide la frontera.'
  }
  return 'Opcional si indicas la frontera. Elegirla antes de sugerir ayuda a la IA a acertar.'
}

// Con propuesta de la IA vigente no hay pista: la sustituye el aviso destacado.
export function pistaFrontera(sugerenciaVigente: boolean, elegida: boolean): string {
  if (sugerenciaVigente) return ''
  if (elegida) return 'Frontera elegida por ti. Nunca quedará por debajo de la parte de la que hablas.'
  return 'Si no indicas ninguna, la IA la estimará al publicar; si no puede, se usa tu progreso actual.'
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
    if (comparativa.obra && (parteOtra.id || hayPersonajeDeOtraObra(personajes))) {
      extra.obraCruzadaId = comparativa.obra.id
      // Sin parte: el servidor usa la primera aparición de sus personajes enfrentados.
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