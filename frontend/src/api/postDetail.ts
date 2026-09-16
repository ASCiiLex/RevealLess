import { api } from './client'
import type { FeedPost } from './feed'

export interface CommentItem {
  id: number
  user: string
  avatar: string
  text: string
  created_at: string
  parent_id: number | null
  emocion_autor: string | null
  reactions_count: number
  user_reaction: string | null
  replies: CommentItem[]
}

export interface PostDetail {
  post: FeedPost
  post_reaction: string | null
  comments: CommentItem[]
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

export async function addComment(
  postId: number,
  text: string,
  parentId?: number,
  emocionAutor?: string | null
) {
  const formData = new FormData()
  formData.append('post_id', String(postId))
  formData.append('text', text)
  if (parentId) formData.append('parent_id', String(parentId))
  if (emocionAutor) formData.append('emocion_autor', emocionAutor)

  const response = await fetch('/comments/add/', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'X-CSRFToken': getCsrfToken() },
    body: formData,
  })
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