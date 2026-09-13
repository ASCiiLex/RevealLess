import { api } from './client'

export interface NotificationItem {
  id: number
  actor: string
  avatar: string
  verb: string
  url: string
  created_at: string
  seen: boolean
}

export interface NotificationPage {
  results: NotificationItem[]
  has_next: boolean
  page: number
}

export function fetchNotifications(page = 1): Promise<NotificationPage> {
  return api.get<NotificationPage>(`/notificaciones/api/?page=${page}`)
}