import { api } from './client'

export type TipoObra = 'serie' | 'pelicula' | 'especial' | 'ova' | 'corto' | 'manga' | 'libro'

export const TIPOS_OBRA: { valor: TipoObra; etiqueta: string }[] = [
  { valor: 'serie', etiqueta: 'Serie' },
  { valor: 'pelicula', etiqueta: 'Película' },
  { valor: 'especial', etiqueta: 'Especial de TV' },
  { valor: 'ova', etiqueta: 'OVA' },
  { valor: 'corto', etiqueta: 'Corto' },
  { valor: 'manga', etiqueta: 'Manga' },
  { valor: 'libro', etiqueta: 'Libro' },
]

export interface SolicitudObra {
  id: number
  titulo: string
  tipo: TipoObra
  enlace: string
  comentario: string
  estado: 'pendiente' | 'aprobada' | 'rechazada'
  obra_slug: string | null
  creado_en: string
  resuelto_en: string | null
}

export interface DatosSolicitudObra {
  titulo: string
  tipo: TipoObra
  enlace?: string
  comentario?: string
}

export function crearSolicitudObra(datos: DatosSolicitudObra): Promise<SolicitudObra> {
  return api.post<SolicitudObra>('/narrative/api/solicitudes-obra/', datos)
}