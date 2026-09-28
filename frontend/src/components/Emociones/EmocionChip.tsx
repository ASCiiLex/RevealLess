import styles from './EmocionChip.module.css'
import { getEmocion } from '../../constants/emociones'

interface Props {
  value: string | null
  onQuitar: () => void
}

export default function EmocionChip({ value, onQuitar }: Props) {
  const emocion = getEmocion(value)
  if (!emocion) return null

  return (
    <span className={styles.chip} style={{ '--emocion-color': emocion.color } as React.CSSProperties}>
      {emocion.emoji} {emocion.etiqueta}
      <button type="button" className={styles.quitar} onClick={onQuitar} aria-label="Quitar emoción">
        ×
      </button>
    </span>
  )
}