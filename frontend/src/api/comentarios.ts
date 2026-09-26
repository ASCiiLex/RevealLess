import { mapearDetecciones, type DeteccionApi, type ReferenciaCruzadaDetectada } from './publicar'
import { construirFormData, enviarFormData, jsonOError } from './formData'

const AVATAR_POR_DEFECTO = '/static/img/default_profile.jpg'

export interface CommentItem {
  id: number
  user: string
  avatar: string
  text: string
  created_at: string
  parent_id: number | null
  emocion_autor: string | null
  referencia_narrativa_id: number | null
  frontera_spoiler_id: number | null
  frontera_origen: string
  obra_cruzada_id: number | null
  frontera_cruzada_id: number | null
  is_own_comment: boolean
  reactions_count: number
  user_reaction: string | null
  replies: CommentItem[]
}

export interface ComentarioCreado {
  id: number
  user: string
  text: string
  created_at: string
  parent_id: number | null
  emocion_autor: string | null
  referencia_narrativa_id: number | null
  frontera_spoiler_id: number | null
  frontera_origen: string
  obra_cruzada_id: number | null
  frontera_cruzada_id: number | null
  likes_count: number
}

export interface AddCommentOptions {
  parentId?: number
  emocionAutor?: string | null
  referenciaNarrativaId?: number | null
  fronteraSpoilerId?: number | null
  obraCruzadaId?: number | null
  fronteraCruzadaId?: number | null
  descartarReferenciaCruzada?: boolean
}

/** En edición: undefined = sin cambios, null = vaciar el campo ('' en el FormData). */
export interface CommentUpdate {
  text?: string
  emocionAutor?: string | null
  referenciaNarrativaId?: number
  fronteraSpoilerId?: number
  obraCruzadaId?: number | null
  fronteraCruzadaId?: number | null
}

function vaciable<T>(valor: T | null | undefined): T | '' | undefined {
  return valor === undefined ? undefined : valor ?? ''
}

/** Adapta la respuesta de creación al formato del árbol de comentarios. */
export function comentarioDesdeCreado(creado: ComentarioCreado): CommentItem {
  return {
    id: creado.id,
    user: creado.user,
    avatar: AVATAR_POR_DEFECTO,
    text: creado.text,
    created_at: creado.created_at,
    parent_id: creado.parent_id,
    emocion_autor: creado.emocion_autor,
    referencia_narrativa_id: creado.referencia_narrativa_id,
    frontera_spoiler_id: creado.frontera_spoiler_id,
    frontera_origen: creado.frontera_origen,
    obra_cruzada_id: creado.obra_cruzada_id,
    frontera_cruzada_id: creado.frontera_cruzada_id,
    is_own_comment: true,
    reactions_count: 0,
    user_reaction: null,
    replies: [],
  }
}

export async function addComment(
  postId: number,
  text: string,
  opciones: AddCommentOptions = {}
): Promise<ComentarioCreado | ReferenciaCruzadaDetectada> {
  const response = await enviarFormData('/comments/add/', 'POST', construirFormData({
    post_id: postId,
    text,
    parent_id: opciones.parentId,
    emocion_autor: opciones.emocionAutor,
    referencia_narrativa: opciones.referenciaNarrativaId,
    frontera_spoiler: opciones.fronteraSpoilerId,
    obra_cruzada: opciones.obraCruzadaId,
    frontera_cruzada: opciones.fronteraCruzadaId,
    descartar_referencia_cruzada: opciones.descartarReferenciaCruzada,
  }))

  const body = await response.json().catch(() => null)

  if (response.status === 409 && body?.detail === 'referencia_cruzada_detectada') {
    return {
      referenciaCruzadaDetectada: true,
      detecciones: mapearDetecciones(body.detecciones as DeteccionApi[]),
    }
  }
  if (!response.ok) throw body

  return body as ComentarioCreado
}

export async function updateComment(commentId: number, datos: CommentUpdate) {
  const response = await enviarFormData(`/comments/editar/${commentId}/`, 'PATCH', construirFormData({
    text: datos.text,
    emocion_autor: vaciable(datos.emocionAutor),
    referencia_narrativa: datos.referenciaNarrativaId,
    frontera_spoiler: datos.fronteraSpoilerId,
    obra_cruzada: vaciable(datos.obraCruzadaId),
    frontera_cruzada: vaciable(datos.fronteraCruzadaId),
  }))
  return jsonOError(response)
}

export async function deleteComment(commentId: number): Promise<void> {
  const response = await enviarFormData(`/comments/delete/${commentId}/`, 'POST')
  await jsonOError(response)
}