import { api, ApiError } from './client'
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
  // Adaptación de la misma historia: el aviso ofrece «misma escena».
  mismaHistoria: boolean
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
  misma_historia?: boolean
}

export interface ObraPublicable {
  id: number
  slug: string
  titulo: string
  imagen_url: string
  adapta_a_id: number | null
}

export interface TemaPublicable {
  id: number
  nombre: string
  obra_slug: string
  obra_titulo: string
}

export interface BibliotecaPublicar {
  obras: ObraPublicable[]
  temas: TemaPublicable[]
}

export interface PersonajePublicable {
  id: number
  nombre: string
  imagen_url: string
}

export interface UnidadSugerida {
  id: number
  etiqueta: string
}

// Propuesta de la IA antes de publicar. frontera null solo si la IA falló;
// fiable=false si no supera el umbral (se muestra igual, con aviso).
export interface SugerenciaFrontera {
  frontera: UnidadSugerida | null
  parte: UnidadSugerida | null
  confianza: number
  fiable: boolean
}

export type ModoCruce = 'comparativa' | 'misma_escena'

export interface DatosPost {
  text: string
  image?: File | null
  // Galería de 2 a 4 imágenes: etiqueta y encuadre por posición.
  imagenes?: File[]
  etiquetas?: string[]
  enfoquesX?: number[]
  enfoquesY?: number[]
  zooms?: number[]
  disposicion?: string
  // Parte, tema o frontera: al menos uno de los tres.
  referenciaNarrativaId?: number | null
  fronteraSpoilerId?: number | null
  // Propuesta de la IA vista antes de publicar: si coincide con la frontera, queda con origen IA.
  fronteraSugeridaIaId?: number | null
  iaConfianza?: number | null
  nivelSpoiler?: string
  emocionAutor?: string | null
  temaId?: number | null
  // Tema escrito a mano: se asigna si existe; si no, queda como solicitud pendiente.
  temaPropuesto?: string
  nuevoProgresoId?: number | null
  confirmarSaltoProgreso?: boolean
  obraCruzadaId?: number | null
  fronteraCruzadaId?: number | null
  modoCruce?: ModoCruce
  descartarReferenciaCruzada?: boolean
  personajesComparadosIds?: number[]
  personajesPropuestos?: string[]
}

type ResultadoConflicto = ProgresoRequerido | RequiereConfirmacionProgreso | ReferenciaCruzadaDetectada

interface CuerpoConflicto {
  detail?: string
  requiere_confirmacion_progreso?: boolean
  obra_slug?: string
  salto?: number
  detecciones?: DeteccionApi[]
}

// Adaptaciones directas o hermanas: mismo criterio que posts.models.misma_historia.
export function mismaHistoria(a: ObraPublicable, b: ObraPublicable): boolean {
  return (
    a.adapta_a_id === b.id
    || b.adapta_a_id === a.id
    || (a.adapta_a_id !== null && a.adapta_a_id === b.adapta_a_id)
  )
}

// Solo la biblioteca del usuario: se carga una vez y se filtra en cliente.
export function fetchObrasPublicar(): Promise<BibliotecaPublicar> {
  return api.get<BibliotecaPublicar>('/narrative/api/obras/publicar/')
}

// Personajes ya aparecidos según el progreso del usuario en esa obra.
export function fetchPersonajesPublicar(obraSlug: string, q = ''): Promise<PersonajePublicable[]> {
  const params = q ? `?q=${encodeURIComponent(q)}` : ''
  return api
    .get<{ personajes: PersonajePublicable[] }>(`/narrative/api/obras/${obraSlug}/personajes-publicar/${params}`)
    .then((data) => data.personajes)
}

export function mapearDetecciones(detecciones: DeteccionApi[] = []): DeteccionCruzada[] {
  return detecciones.map((d) => ({
    obraId: d.obra_id,
    obraTitulo: d.obra_titulo,
    obraSlug: d.obra_slug,
    palabra: d.palabra,
    mismaHistoria: Boolean(d.misma_historia),
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

// desde: obra desde la que se publica, para pedir la frontera de la obra cruzada sin progreso en ella.
export async function sugerirFrontera(
  obraSlug: string, texto: string, referenciaId: number | null, desde: string | null = null,
): Promise<SugerenciaFrontera> {
  const response = await enviarFormData(`/posts/api/sugerir-frontera/${obraSlug}/`, 'POST', construirFormData({
    text: texto,
    referencia_narrativa: referenciaId,
    desde,
  }))
  const body = await response.json().catch(() => null)
  if (!response.ok) throw new ApiError(response.status, body)
  return body as SugerenciaFrontera
}

export async function crearPost(obraSlug: string, datos: DatosPost): Promise<PostCreado | ResultadoConflicto> {
  const response = await enviarFormData(`/posts/api/crear/${obraSlug}/`, 'POST', construirFormData({
    text: datos.text,
    image: datos.image,
    imagenes: datos.imagenes,
    etiquetas: datos.etiquetas,
    enfoques_x: datos.enfoquesX,
    enfoques_y: datos.enfoquesY,
    zooms: datos.zooms,
    disposicion: datos.disposicion,
    referencia_narrativa: datos.referenciaNarrativaId,
    frontera_spoiler: datos.fronteraSpoilerId,
    frontera_sugerida_ia: datos.fronteraSugeridaIaId,
    ia_confianza: datos.iaConfianza,
    nivel_spoiler: datos.nivelSpoiler,
    emocion_autor: datos.emocionAutor,
    tema: datos.temaId,
    tema_propuesto: datos.temaPropuesto,
    nuevo_progreso: datos.nuevoProgresoId,
    confirmar_salto_progreso: datos.confirmarSaltoProgreso,
    obra_cruzada: datos.obraCruzadaId,
    frontera_cruzada: datos.fronteraCruzadaId,
    modo_cruce: datos.modoCruce,
    descartar_referencia_cruzada: datos.descartarReferenciaCruzada,
    personajes_comparados: datos.personajesComparadosIds,
    personajes_propuestos: datos.personajesPropuestos,
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