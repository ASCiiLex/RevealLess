export interface Emocion {
  clave: string
  emoji: string
  etiqueta: string
  color: string
}

export const EMOCIONES: Emocion[] = [
  { clave: 'me_gusta', emoji: '👍', etiqueta: 'Me gusta', color: 'var(--emocion-gusta)' },
  { clave: 'me_encanta', emoji: '❤️', etiqueta: 'Me encanta', color: 'var(--emocion-encanta)' },
  { clave: 'me_divierte', emoji: '😂', etiqueta: 'Me divierte', color: 'var(--emocion-divierte)' },
  { clave: 'me_sorprende', emoji: '😲', etiqueta: 'Me sorprende', color: 'var(--emocion-sorprende)' },
  { clave: 'me_enfada', emoji: '😡', etiqueta: 'Me enfada', color: 'var(--emocion-enfada)' },
  { clave: 'me_da_asco', emoji: '🤢', etiqueta: 'Me da asco', color: 'var(--emocion-asco)' },
  { clave: 'me_entristece', emoji: '😢', etiqueta: 'Me entristece', color: 'var(--emocion-entristece)' },
  { clave: 'me_entusiasma', emoji: '🤩', etiqueta: 'Me entusiasma', color: 'var(--emocion-entusiasma)' },
  { clave: 'me_emociona', emoji: '🥹', etiqueta: 'Me emociona', color: 'var(--emocion-emociona)' },
  { clave: 'me_da_curiosidad', emoji: '🤔', etiqueta: 'Me da curiosidad', color: 'var(--emocion-curiosidad)' },
  { clave: 'me_da_miedo', emoji: '😨', etiqueta: 'Me da miedo', color: 'var(--emocion-miedo)' },
]

export function getEmocion(clave: string | null | undefined): Emocion | undefined {
  return EMOCIONES.find((e) => e.clave === clave)
}