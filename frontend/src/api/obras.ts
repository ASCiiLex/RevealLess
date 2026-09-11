import { api } from './client'
import type { LomoObra } from '../components/Carousel/Lomo'

export interface CatalogoObras {
  biblioteca: LomoObra[]
  descubrir: LomoObra[]
}

export function fetchCatalogoObras(): Promise<CatalogoObras> {
  return api.get<CatalogoObras>('/narrative/api/obras/')
}