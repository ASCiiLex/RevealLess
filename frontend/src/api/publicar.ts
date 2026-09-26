import { ApiError } from './client'
import type { UnidadNarrativa } from './progreso'
import { construirFormData, enviarFormData } from './formData'

export interface ProgresoRequerido {
  progresoRequerido: true
  obraSlug: string
}

export interface RequiereConfirmacionProgreso {
  requiereConfirmacion: true
  detail: string
  salto: number
}

export interface DeteccionCruzada {
  obraId: number
  obraTitulo: string
  obraSlug: string
  palabra: string
}

export interface ReferenciaCruzadaDetectada {
  referenciaCruzadaDetectada: true
  detecciones: DeteccionCruzada[]
}

export interface PostCreado {
  id: number
}

export interface DeteccionApi {
  obra_id: number
  obra_titulo: string
  obra_slug: string
  palabra: string
}

export interface DatosPost {
  text: string
  image?: File | null
  referenciaNarrativaId: number
  fronteraSpoilerId?: number | null
  nivelSpoiler?: string
  emocionAutor?: string | null
  temaId?: number | null
  nuevoProgresoId?: number | null
  confirmarSaltoProgreso?: boolean
  obraCruzadaId?: number | null
  fronteraCruzadaId?: number | null
  descartarReferenciaCruzada?: boolean
}

type ResultadoConflicto = ProgresoRequerido | RequiereConfirmacionProgreso | ReferenciaCruzadaDetectada

interface CuerpoConflicto {
  detail?: string
  requiere_confirmacion_progreso?: boolean
  obra_slug?: string
  salto?: number
  detecciones?: DeteccionApi[]
}

export function mapearDetecciones(detecciones: DeteccionApi[] = []): DeteccionCruzada[] {
  return detecciones.map((d) => ({
    obraId: d.obra_id,
    obraTitulo: d.obra_titulo,
    obraSlug: d.obra_slug,
    palabra: d.palabra,
  }))
}

function interpretarConflicto(body: CuerpoConflicto, obraSlug: string): ResultadoConflicto | null {
  if (body.detail === 'progreso_requerido') {
    return { progresoRequerido: true, obraSlug: body.obra_slug ?? obraSlug }
  }
  if (body.requiere_confirmacion_progreso) {
    return { requiereConfirmacion: true, detail: body.detail ?? '', salto: body.salto ?? 0 }
  }
  if (body.detail === 'referencia_cruzada_detectada') {
    return { referenciaCruzadaDetectada: true, detecciones: mapearDetecciones(body.detecciones) }
  }
  return null
}

export async function crearPost(obraSlug: string, datos: DatosPost): Promise<PostCreado | ResultadoConflicto> {
  const response = await enviarFormData(`/posts/api/crear/${obraSlug}/`, 'POST', construirFormData({
    text: datos.text,
    image: datos.image,
    referencia_narrativa: datos.referenciaNarrativaId,
    frontera_spoiler: datos.fronteraSpoilerId,
    nivel_spoiler: datos.nivelSpoiler,
    emocion_autor: datos.emocionAutor,
    tema: datos.temaId,
    nuevo_progreso: datos.nuevoProgresoId,
    confirmar_salto_progreso: datos.confirmarSaltoProgreso,
    obra_cruzada: datos.obraCruzadaId,
    frontera_cruzada: datos.fronteraCruzadaId,
    descartar_referencia_cruzada: datos.descartarReferenciaCruzada,
  }))

  const body = await response.json().catch(() => null)

  if (response.status === 409 && body) {
    const conflicto = interpretarConflicto(body as CuerpoConflicto, obraSlug)
    if (conflicto) return conflicto
  }
  if (!response.ok) throw new ApiError(response.status, body)

  return body as PostCreado
}

export type { UnidadNarrativa }