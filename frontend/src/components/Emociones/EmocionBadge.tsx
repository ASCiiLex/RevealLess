import { getEmocion } from '../../constants/emociones'

interface Props {
  emocionAutor: string | null | undefined
}

export default function EmocionBadge({ emocionAutor }: Props) {
  const emocion = getEmocion(emocionAutor ?? undefined)
  if (!emocion) return null

  return (
    <span aria-label={emocion.etiqueta} title={emocion.etiqueta} style={{ fontSize: 14 }}>
      {emocion.emoji}
    </span>
  )
}