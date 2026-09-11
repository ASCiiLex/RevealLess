import { api, ApiError } from './client'

export interface UnidadNarrativa {
  id: number
  nombre: string
  tipo: string
  etiqueta: string
  orden_inicio: number
  orden_fin: number
  imagen: string
  padre: number | null
}

export interface Progreso {
  unidad_actual: UnidadNarrativa
  orden_absoluto: number
}

export interface ProgresoData {
  obra: { titulo: string; slug: string }
  unidades: UnidadNarrativa[]
  progreso: Progreso | null
}

interface ActualizarProgresoOk {
  unidad_actual: UnidadNarrativa
  orden_absoluto: number
}

export interface RequiereConfirmacion {
  requiereConfirmacion: true
  detail: string
  salto: number
}

interface SaltoGrandeBody {
  detail: string
  requiere_confirmacion: true
  salto: number
}

export function fetchProgreso(obraSlug: string): Promise<ProgresoData> {
  return api.get<ProgresoData>(`/narrative/api/progreso/${obraSlug}/`)
}

export async function actualizarProgreso(
  obraSlug: string,
  unidadId: number,
  confirmado = false
): Promise<ActualizarProgresoOk | RequiereConfirmacion> {
  try {
    return await api.post<ActualizarProgresoOk>(`/narrative/api/progreso/${obraSlug}/`, {
      unidad_actual: unidadId,
      confirmado,
    })
  } catch (err) {
    if (err instanceof ApiError && err.status === 409) {
      const body = err.detail as SaltoGrandeBody
      return {
        requiereConfirmacion: true,
        detail: body.detail,
        salto: body.salto,
      }
    }
    throw err
  }
}