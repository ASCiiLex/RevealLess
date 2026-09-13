import { api } from './client'
import type { FeedPost } from './feed'

export interface CommentItem {
  id: number
  user: string
  avatar: string
  text: string
  created_at: string
  parent_id: number | null
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

/** Reutiliza el endpoint JSON existente de Django clasico
 * (toggle_reaction_post), no un endpoint DRF nuevo -- ya devuelve JSON,
 * ya valida CSRF, y funciona igual desde fetch() que desde el JS
 * original (likes.js). */
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

export async function addComment(postId: number, text: string, parentId?: number) {
  const formData = new FormData()
  formData.append('post_id', String(postId))
  formData.append('text', text)
  if (parentId) formData.append('parent_id', String(parentId))

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