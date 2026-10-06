type ValorCampo = string | number | boolean | File | null | undefined

export function getCsrfToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : ''
}

function anadir(formData: FormData, clave: string, valor: ValorCampo) {
  if (valor === null || valor === undefined || valor === false) return
  formData.append(clave, valor instanceof File ? valor : String(valor))
}

/** Omite null, undefined y false. '' se envía: permite vaciar campos como emocion_autor.
 * Las listas se envían como claves repetidas (galería, etiquetas, personajes). */
export function construirFormData(campos: Record<string, ValorCampo | ValorCampo[]>): FormData {
  const formData = new FormData()
  for (const [clave, valor] of Object.entries(campos)) {
    if (Array.isArray(valor)) valor.forEach((v) => anadir(formData, clave, v))
    else anadir(formData, clave, valor)
  }
  return formData
}

export function enviarFormData(url: string, method: 'POST' | 'PATCH', body?: FormData): Promise<Response> {
  return fetch(url, {
    method,
    credentials: 'same-origin',
    headers: { 'X-CSRFToken': getCsrfToken() },
    body,
  })
}

export async function jsonOError<T>(response: Response): Promise<T> {
  const body = await response.json().catch(() => null)
  if (!response.ok) throw body
  return body as T
}