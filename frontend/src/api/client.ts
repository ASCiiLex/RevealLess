// Cliente fetch mínimo: same-origin (React embebido en página Django),
// añade el token CSRF leído de la cookie en cada método mutante.
// Requiere CSRF_COOKIE_HTTPONLY=False en settings.py (ver commit previo).

function getCsrfToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : ''
}

interface ApiOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
}

async function request<T>(url: string, options: ApiOptions = {}): Promise<T> {
  const method = (options.method ?? 'GET').toUpperCase()
  const headers = new Headers(options.headers)

  if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json')
  }
  if (method !== 'GET' && method !== 'HEAD') {
    headers.set('X-CSRFToken', getCsrfToken())
  }

  const response = await fetch(url, {
    ...options,
    method,
    headers,
    credentials: 'same-origin',
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  })

  if (!response.ok) {
    const detail = await response.json().catch(() => null)
    throw new ApiError(response.status, detail)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(status: number, detail: unknown) {
    super(`API error ${status}`)
    this.status = status
    this.detail = detail
  }
}

export const api = {
  get: <T>(url: string) => request<T>(url),
  post: <T>(url: string, body?: unknown) => request<T>(url, { method: 'POST', body }),
  patch: <T>(url: string, body?: unknown) => request<T>(url, { method: 'PATCH', body }),
  delete: <T>(url: string) => request<T>(url, { method: 'DELETE' }),
}