import { api } from './client'
import type { ImagenPost } from './feed'

export interface SavedPost {
  id: number
  post_id: number
  text: string
  // Composición del post (galería con encuadre o imagen simple); vacía si no tiene fotos.
  imagenes: ImagenPost[]
  disposicion: string
  created_at: string
}

export interface EstadoGuardado {
  is_saved: boolean
}

export function fetchSavedPosts(): Promise<SavedPost[]> {
  return api.get<SavedPost[]>('/guardados/api/')
}

export function guardarPost(postId: number): Promise<EstadoGuardado> {
  return api.post<EstadoGuardado>(`/guardados/api/${postId}/`)
}

export function quitarGuardado(postId: number): Promise<EstadoGuardado> {
  return api.delete<EstadoGuardado>(`/guardados/api/${postId}/`)
}