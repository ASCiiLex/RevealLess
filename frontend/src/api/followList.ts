import { api } from './client'

export interface FollowUserItem {
  username: string
  avatar_url: string
}

export function fetchFollowers(username: string): Promise<FollowUserItem[]> {
  return api.get<FollowUserItem[]>(`/follows/api/${username}/seguidores/`)
}

export function fetchFollowing(username: string): Promise<FollowUserItem[]> {
  return api.get<FollowUserItem[]>(`/follows/api/${username}/siguiendo/`)
}