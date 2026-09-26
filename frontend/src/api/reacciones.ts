import { construirFormData, enviarFormData } from './formData'

export interface PostReactionsTotals {
  totals: Record<string, number>
}

async function toggle(url: string, campos: Record<string, string | number>) {
  const response = await enviarFormData(url, 'POST', construirFormData(campos))
  return response.json()
}

export function toggleReactionPost(postId: number, reaction: string) {
  return toggle('/posts/reaction/', { post_id: postId, reaction })
}

export function toggleReactionComment(commentId: number, reaction: string) {
  return toggle(`/comments/${commentId}/reaction/`, { reaction })
}

export function toggleReactionMessage(messageId: number, reaction: string) {
  return toggle(`/mensajes/${messageId}/reaction/`, { reaction })
}

export async function fetchPostReactionsTotals(postId: number): Promise<PostReactionsTotals> {
  const response = await fetch(`/posts/reactions/${postId}/`, { credentials: 'same-origin' })
  return response.json()
}