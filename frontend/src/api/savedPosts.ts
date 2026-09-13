import { api } from './client'

export interface SavedPost {
  id: number
  post_id: number
  image_url: string
  created_at: string
}

export function fetchSavedPosts(): Promise<SavedPost[]> {
  return api.get<SavedPost[]>('/guardados/api/')
}