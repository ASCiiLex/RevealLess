import styles from './EmocionPopover.module.css'
import { EMOCIONES } from '../../constants/emociones'

interface Props {
  visible: boolean
  value: string | null
  onSelect: (clave: string | null) => void
  direccion?: 'arriba' | 'abajo'
}

export default function EmocionPopover({ visible, value, onSelect, direccion = 'arriba' }: Props) {
  if (!visible) return null

  return (
    <div
      className={`${styles.panel} ${direccion === 'abajo' ? styles.panelAbajo : ''}`}
      onMouseDown={(e) => e.preventDefault()}
    >
      <div className={styles.grid}>
        {EMOCIONES.map((emocion) => (
          <button
            key={emocion.clave}
            type="button"
            className={`${styles.opcion} ${value === emocion.clave ? styles.opcionActiva : ''}`}
            style={{ '--emocion-color': emocion.color } as React.CSSProperties}
            title={emocion.etiqueta}
            onClick={() => onSelect(value === emocion.clave ? null : emocion.clave)}
          >
            {emocion.emoji}
          </button>
        ))}
      </div>
    </div>
  )
}