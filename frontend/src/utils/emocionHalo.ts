import { getEmocion } from '../constants/emociones'
import type { CSSProperties } from 'react'

type Tamano = 'post' | 'comentario'

// borde (px), brillo cercano y difuso (blur en px)
const HALO: Record<Tamano, { borde: number; brillo: number; difuso: number }> = {
  post: { borde: 3, brillo: 12, difuso: 28 },
  comentario: { borde: 2, brillo: 8, difuso: 18 },
}

const SOMBRA_BASE = '0 4px 10px rgba(0, 0, 0, 0.12)'

export function emocionHaloStyle(
  emocionAutor: string | null | undefined,
  tamano: Tamano = 'post',
): CSSProperties {
  const emocion = getEmocion(emocionAutor ?? undefined)
  if (!emocion) return {}

  const { borde, brillo, difuso } = HALO[tamano]
  const c = emocion.color

  return {
    border: `${borde}px solid ${c}`,
    boxShadow: [
      `0 0 ${brillo}px color-mix(in srgb, ${c} 75%, transparent)`,
      `0 0 ${difuso}px color-mix(in srgb, ${c} 45%, transparent)`,
      `inset 0 0 ${Math.round(brillo / 2)}px color-mix(in srgb, ${c} 25%, transparent)`,
      SOMBRA_BASE,
    ].join(', '),
  }
}