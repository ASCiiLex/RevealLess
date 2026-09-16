import styles from './EmocionSelector.module.css'
import { EMOCIONES } from '../../constants/emociones'

interface Props {
  value: string | null
  onChange: (clave: string | null) => void
  label?: string
}

export default function EmocionSelector({ value, onChange, label = '¿Qué te produce esto? (opcional)' }: Props) {
  return (
    <div className={styles.wrapper}>
      <span className={styles.label}>{label}</span>
      <div className={styles.grid}>
        {EMOCIONES.map((emocion) => (
          <button
            key={emocion.clave}
            type="button"
            className={`${styles.opcion} ${value === emocion.clave ? styles.opcionActiva : ''}`}
            style={{ '--emocion-color': emocion.color } as React.CSSProperties}
            onClick={() => onChange(value === emocion.clave ? null : emocion.clave)}
            aria-pressed={value === emocion.clave}
          >
            <span className={styles.emoji} aria-hidden="true">{emocion.emoji}</span>
            <span className={styles.etiqueta}>{emocion.etiqueta}</span>
          </button>
        ))}
      </div>
      {value && (
        <button type="button" className={styles.limpiar} onClick={() => onChange(null)}>
          Quitar emoción
        </button>
      )}
    </div>
  )
}