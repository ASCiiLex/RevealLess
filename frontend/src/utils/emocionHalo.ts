import { getEmocion } from '../constants/emociones'
import type { CSSProperties } from 'react'

export function emocionHaloStyle(emocionAutor: string | null | undefined): CSSProperties {
  const emocion = getEmocion(emocionAutor ?? undefined)
  if (!emocion) return {}
  return { borderColor: emocion.color, borderWidth: 3, borderStyle: 'solid' }
}