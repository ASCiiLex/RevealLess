import { api } from './client'

export interface Me {
  username: string
  avatar_url: string
  unread_notifications: number
  unread_messages: number
  unread_count: number
}

export function fetchMe(): Promise<Me> {
  return api.get<Me>('/api/me/')
}