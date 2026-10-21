import { api } from './client'
import type { FeedPost } from './feed'
import type { CommentItem } from './comentarios'
import { construirFormData, enviarFormData, jsonOError } from './formData'

// Reexportados para no romper importadores existentes.
export * from './comentarios'
export * from './reacciones'

export interface PostDetail {
  post: FeedPost
  post_reaction: string | null
  comments: CommentItem[]
}

export function fetchPostDetail(postId: number, sort = 'recent'): Promise<PostDetail> {
  return api.get<PostDetail>(`/posts/api/${postId}/?sort=${sort}`)
}

export async function updatePost(
  postId: number,
  datos: {
    text?: string
    image?: File | null
    quitarImagen?: boolean
    // Enlace nuevo: sustituye al vídeo actual. quitarVideo lo retira.
    videoUrl?: string
    quitarVideo?: boolean
    referenciaNarrativaId?: number
    fronteraSpoilerId?: number | null
    nivelSpoiler?: string
    emocionAutor?: string | null
  }
): Promise<FeedPost> {
  const response = await enviarFormData(`/posts/api/${postId}/editar/`, 'PATCH', construirFormData({
    text: datos.text,
    image: datos.image,
    // Solo se envía cuando hay que retirar la imagen actual.
    quitar_imagen: datos.quitarImagen ? 'true' : undefined,
    video_url: datos.videoUrl,
    quitar_video: datos.quitarVideo ? 'true' : undefined,
    referencia_narrativa: datos.referenciaNarrativaId,
    frontera_spoiler: datos.fronteraSpoilerId,
    nivel_spoiler: datos.nivelSpoiler,
    emocion_autor: datos.emocionAutor === undefined ? undefined : datos.emocionAutor ?? '',
  }))
  return jsonOError<FeedPost>(response)
}