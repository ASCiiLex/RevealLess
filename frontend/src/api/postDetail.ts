import { api } from './client'
import type { FeedPost } from './feed'
import type { ReferenciaCruzadaDetectada } from './publicar'

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

export interface PostDetail {
  post: FeedPost
  post_reaction: string | null
  comments: CommentItem[]
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

export function fetchPostDetail(postId: number, sort = 'recent'): Promise<PostDetail> {
  return api.get<PostDetail>(`/posts/api/${postId}/?sort=${sort}`)
}

function getCsrfToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : ''
}

export async function toggleReactionPost(postId: number, reaction: string) {
  const formData = new FormData()
  formData.append('post_id', String(postId))
  formData.append('reaction', reaction)

  const response = await fetch('/posts/react/', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'X-CSRFToken': getCsrfToken() },
    body: formData,
  })
  return response.json()
}

export interface PostReactionsTotals {
  totals: Record<string, number>
}

export async function fetchPostReactionsTotals(postId: number): Promise<PostReactionsTotals> {
  const response = await fetch(`/posts/reactions/${postId}/`, {
    credentials: 'same-origin',
  })
  return response.json()
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

export async function addComment(
  postId: number,
  text: string,
  opciones: AddCommentOptions = {}
): Promise<ComentarioCreado | ReferenciaCruzadaDetectada> {
  const formData = new FormData()
  formData.append('post_id', String(postId))
  formData.append('text', text)
  if (opciones.parentId) formData.append('parent_id', String(opciones.parentId))
  if (opciones.emocionAutor) formData.append('emocion_autor', opciones.emocionAutor)
  if (opciones.referenciaNarrativaId) formData.append('referencia_narrativa', String(opciones.referenciaNarrativaId))
  if (opciones.fronteraSpoilerId) formData.append('frontera_spoiler', String(opciones.fronteraSpoilerId))
  if (opciones.obraCruzadaId) formData.append('obra_cruzada', String(opciones.obraCruzadaId))
  if (opciones.fronteraCruzadaId) formData.append('frontera_cruzada', String(opciones.fronteraCruzadaId))
  if (opciones.descartarReferenciaCruzada) formData.append('descartar_referencia_cruzada', 'true')

  const response = await fetch('/comments/add/', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'X-CSRFToken': getCsrfToken() },
    body: formData,
  })

  const body = await response.json().catch(() => null)

  if (!response.ok) {
    if (response.status === 409 && body?.detail === 'referencia_cruzada_detectada') {
      return {
        referenciaCruzadaDetectada: true,
        detecciones: (body.detecciones ?? []).map((d: any) => ({
          obraId: d.obra_id,
          obraTitulo: d.obra_titulo,
          obraSlug: d.obra_slug,
          palabra: d.palabra,
        })),
      }
    }
    throw body
  }

  return body
}

export async function updateComment(
  commentId: number,
  datos: {
    text?: string
    emocionAutor?: string | null
    referenciaNarrativaId?: number
    fronteraSpoilerId?: number | null
    obraCruzadaId?: number | null
    fronteraCruzadaId?: number | null
  }
) {
  const formData = new FormData()
  if (datos.text !== undefined) formData.append('text', datos.text)
  if (datos.emocionAutor !== undefined) formData.append('emocion_autor', datos.emocionAutor ?? '')
  if (datos.referenciaNarrativaId) formData.append('referencia_narrativa', String(datos.referenciaNarrativaId))
  if (datos.fronteraSpoilerId) formData.append('frontera_spoiler', String(datos.fronteraSpoilerId))
  if (datos.obraCruzadaId) formData.append('obra_cruzada', String(datos.obraCruzadaId))
  if (datos.fronteraCruzadaId) formData.append('frontera_cruzada', String(datos.fronteraCruzadaId))

  const response = await fetch(`/comments/editar/${commentId}/`, {
    method: 'PATCH',
    credentials: 'same-origin',
    headers: { 'X-CSRFToken': getCsrfToken() },
    body: formData,
  })

  if (!response.ok) {
    const detail = await response.json().catch(() => null)
    throw detail
  }
  return response.json()
}

export async function toggleReactionComment(commentId: number, reaction: string) {
  const formData = new FormData()
  formData.append('reaction', reaction)

  const response = await fetch(`/comments/react/${commentId}/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'X-CSRFToken': getCsrfToken() },
    body: formData,
  })
  return response.json()
}

export async function toggleReactionMessage(messageId: number, reaction: string) {
  const formData = new FormData()
  formData.append('reaction', reaction)

  const response = await fetch(`/mensajes/react/msg/${messageId}/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'X-CSRFToken': getCsrfToken() },
    body: formData,
  })
  return response.json()
}

export async function updatePost(
  postId: number,
  datos: {
    text?: string
    image?: File | null
    referenciaNarrativaId?: number
    fronteraSpoilerId?: number | null
    nivelSpoiler?: string
    emocionAutor?: string | null
  }
): Promise<FeedPost> {
  const formData = new FormData()
  if (datos.text !== undefined) formData.append('text', datos.text)
  if (datos.image) formData.append('image', datos.image)
  if (datos.referenciaNarrativaId) formData.append('referencia_narrativa', String(datos.referenciaNarrativaId))
  if (datos.fronteraSpoilerId) formData.append('frontera_spoiler', String(datos.fronteraSpoilerId))
  if (datos.nivelSpoiler) formData.append('nivel_spoiler', datos.nivelSpoiler)
  if (datos.emocionAutor !== undefined) formData.append('emocion_autor', datos.emocionAutor ?? '')

  const response = await fetch(`/posts/api/${postId}/editar/`, {
    method: 'PATCH',
    credentials: 'same-origin',
    headers: { 'X-CSRFToken': getCsrfToken() },
    body: formData,
  })

  if (!response.ok) {
    const detail = await response.json().catch(() => null)
    throw detail
  }
  return response.json()
}

export async function deleteComment(commentId: number): Promise<void> {
  const response = await fetch(`/comments/delete/${commentId}/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'X-CSRFToken': getCsrfToken() },
  })
  if (!response.ok) {
    const detail = await response.json().catch(() => null)
    throw detail
  }
}