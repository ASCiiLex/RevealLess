import { ApiError } from './client'
import type { UnidadNarrativa } from './progreso'

export interface ProgresoRequerido {
  progresoRequerido: true
  obraSlug: string
}

export interface RequiereConfirmacionProgreso {
  requiereConfirmacion: true
  detail: string
  salto: number
}

export interface PostCreado {
  id: number
}

function getCsrfToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : ''
}

export async function crearPost(
  obraSlug: string,
  datos: {
    text: string
    image?: File | null
    referenciaNarrativaId: number
    fronteraSpoilerId?: number | null
    nivelSpoiler?: string
    emocionAutor?: string | null
    nuevoProgresoId?: number | null
    confirmarSaltoProgreso?: boolean
  }
): Promise<PostCreado | ProgresoRequerido | RequiereConfirmacionProgreso> {
  const formData = new FormData()
  formData.append('text', datos.text)
  if (datos.image) formData.append('image', datos.image)
  formData.append('referencia_narrativa', String(datos.referenciaNarrativaId))
  if (datos.fronteraSpoilerId) formData.append('frontera_spoiler', String(datos.fronteraSpoilerId))
  if (datos.nivelSpoiler) formData.append('nivel_spoiler', datos.nivelSpoiler)
  if (datos.emocionAutor) formData.append('emocion_autor', datos.emocionAutor)
  if (datos.nuevoProgresoId) formData.append('nuevo_progreso', String(datos.nuevoProgresoId))
  if (datos.confirmarSaltoProgreso) formData.append('confirmar_salto_progreso', 'true')

  try {
    const response = await fetch(`/posts/api/crear/${obraSlug}/`, {
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
  } catch (err) {
    if (err instanceof ApiError && err.status === 409) {
      const body = err.detail as { detail: string; requiere_confirmacion_progreso?: boolean; obra_slug?: string }
      if (body.detail === 'progreso_requerido') {
        return { progresoRequerido: true, obraSlug: body.obra_slug ?? obraSlug }
      }
      if (body.requiere_confirmacion_progreso) {
        const saltoBody = err.detail as { detail: string; salto: number }
        return { requiereConfirmacion: true, detail: saltoBody.detail, salto: saltoBody.salto }
      }
    }
    throw err
  }
}

export type { UnidadNarrativa }