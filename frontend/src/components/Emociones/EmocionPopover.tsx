import { useEffect, useRef, useState, type RefObject } from 'react'
import styles from './EmocionPopover.module.css'
import { EMOCIONES } from '../../constants/emociones'

// Margen para el bottom nav fijo, igual criterio que ReactionBar.
const ALTURA_BOTTOM_NAV = 64
const ALTURA_PANEL_ESTIMADA = 120

interface Props {
  visible: boolean
  value: string | null
  onSelect: (clave: string | null) => void
  anchorRef?: RefObject<HTMLElement>
}

export default function EmocionPopover({ visible, value, onSelect, anchorRef }: Props) {
  const [posicion, setPosicion] = useState<'abajo' | 'arriba'>('abajo')
  const yaMedido = useRef(false)

  useEffect(() => {
    if (!visible) {
      yaMedido.current = false
      return
    }
    if (yaMedido.current || !anchorRef?.current) return

    const rect = anchorRef.current.getBoundingClientRect()
    const espacioAbajo = window.innerHeight - rect.bottom - ALTURA_BOTTOM_NAV
    setPosicion(espacioAbajo < ALTURA_PANEL_ESTIMADA ? 'arriba' : 'abajo')
    yaMedido.current = true
  }, [visible, anchorRef])

  if (!visible) return null

  return (
    <div
      className={`${styles.panel} ${posicion === 'arriba' ? styles.panelArriba : ''}`}
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