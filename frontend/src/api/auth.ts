import { api, ApiError } from './client'

function getCsrfToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : ''
}

export interface LoginResponse {
  username: string
}

export function login(username: string, password: string): Promise<LoginResponse> {
  return api.post<LoginResponse>('/cuentas/api/login/', { username, password })
}

export async function logout(): Promise<void> {
  await api.post<void>('/cuentas/logout/')
}

export interface RegisterData {
  username: string
  email: string
  password: string
  password2: string
  image?: File | null
}

export async function register(data: RegisterData): Promise<LoginResponse> {
  const formData = new FormData()
  formData.append('username', data.username)
  formData.append('email', data.email)
  formData.append('password', data.password)
  formData.append('password2', data.password2)
  if (data.image) {
    formData.append('image', data.image)
  }

  const response = await fetch('/cuentas/api/register/', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'X-CSRFToken': getCsrfToken() },
    body: formData,
  })

  if (!response.ok) {
    const detail = await response.json().catch(() => null)
    throw new ApiError(response.status, detail)
  }

  return response.json()
}