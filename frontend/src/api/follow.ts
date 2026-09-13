import { api } from './client'

export function seguirUsuario(username: string): Promise<{ is_following: boolean }> {
  return api.post<{ is_following: boolean }>(`/follows/api/${username}/`)
}

export function dejarDeSeguirUsuario(username: string): Promise<{ is_following: boolean }> {
  return api.delete<{ is_following: boolean }>(`/follows/api/${username}/`)
}