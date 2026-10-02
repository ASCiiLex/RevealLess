import { api } from './client'

export interface ProfilePost {
  id: number
  image_url: string | null
  text: string
}

export interface ProfileDetail {
  username: string
  bio: string
  interests: string
  avatar_url: string
  is_own_profile: boolean
  is_following: boolean
  followers_count: number
  following_count: number
  posts: ProfilePost[]
  has_hidden_posts: boolean
}

export interface ProfileEditData {
  username: string
  email: string
  bio: string
  interests: string
  avatar_url: string
}

export function fetchProfile(username: string): Promise<ProfileDetail> {
  return api.get<ProfileDetail>(`/perfil/api/${username}/`)
}

export function fetchProfileEditData(): Promise<ProfileEditData> {
  return api.get<ProfileEditData>('/perfil/api/editar/')
}

export function updateProfile(data: {
  username: string
  email: string
  bio?: string
  interests?: string
  image?: File | null
}): Promise<ProfileEditData> {
  const formData = new FormData()
  formData.append('username', data.username)
  formData.append('email', data.email)
  if (data.bio !== undefined) formData.append('bio', data.bio)
  if (data.interests !== undefined) formData.append('interests', data.interests)
  if (data.image) formData.append('image', data.image)

  return fetch('/perfil/api/editar/', {
    method: 'PATCH',
    credentials: 'same-origin',
    headers: { 'X-CSRFToken': getCsrfToken() },
    body: formData,
  }).then(async (res) => {
    if (!res.ok) {
      const detail = await res.json().catch(() => null)
      throw detail
    }
    return res.json()
  })
}

function getCsrfToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : ''
}