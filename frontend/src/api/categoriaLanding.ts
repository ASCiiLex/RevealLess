import { api } from './client'
import type { LomoObra } from '../components/Carousel/Lomo'

export interface CategoriaLanding {
  id: number
  nombre: string
  total_obras: number
  obras: LomoObra[]
}

export function fetchCategoriaLanding(categoriaId: number): Promise<CategoriaLanding> {
  return api.get<CategoriaLanding>(`/narrative/api/categorias/${categoriaId}/`)
}