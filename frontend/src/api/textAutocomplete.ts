import { api } from './client'

export interface MentionSuggestion {
  username: string
}

export interface HashtagSuggestion {
  name: string
}

export function fetchMentionSuggestions(q: string): Promise<{ results: MentionSuggestion[] }> {
  return api.get(`/posts/mentions-search/?q=${encodeURIComponent(q)}`)
}

export function fetchHashtagSuggestions(q: string): Promise<{ results: HashtagSuggestion[] }> {
  return api.get(`/posts/hashtags-search/?q=${encodeURIComponent(q)}`)
}

export function fetchSuggestedHashtags(): Promise<{ results: string[] }> {
  return api.get('/posts/suggested-hashtags/')
}