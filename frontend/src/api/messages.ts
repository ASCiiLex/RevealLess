import { api } from './client'

export interface InboxItem {
  username: string
  avatar: string
  last_message: string
  unread_count: number
}

export interface ChatMessage {
  id: number
  sender: string
  text: string
  created_at: string
}

export interface ChatHistory {
  other: { username: string; avatar: string }
  messages: ChatMessage[]
}

export function fetchInbox(): Promise<InboxItem[]> {
  return api.get<InboxItem[]>('/mensajes/api/')
}

export function fetchChatHistory(username: string): Promise<ChatHistory> {
  return api.get<ChatHistory>(`/mensajes/api/${username}/`)
}