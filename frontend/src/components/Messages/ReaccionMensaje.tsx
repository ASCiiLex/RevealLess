import { useEffect, useRef, useState } from 'react'
import styles from '../Feed/ReactionBar.module.css'
import { toggleReactionMessage } from '../../api/reacciones'
import { EMOCIONES } from '../../constants/emociones'

interface Props {
  messageId: number
  reaccion: string | null
  /** Solo quien recibe el mensaje puede reaccionar; en los propios solo se ve la del otro. */
  editable: boolean
  onCambio: (reaccion: string | null) => void
}

export default function ReaccionMensaje({ messageId, reaccion, editable, onCambio }: Props) {
  const [abierto, setAbierto] = useState(false)
  const [posicion, setPosicion] = useState<'abajo' | 'arriba'>('abajo')
  const wrapperRef = useRef<HTMLDivElement>(null)
  const emocion = EMOCIONES.find((e) => e.clave === reaccion)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setAbierto(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  if (!editable) {
    if (!emocion) return null
    return (
      <div className={styles.wrapper}>
        <span className={`${styles.trigger} ${styles.triggerSutil} ${styles.triggerActive}`}>
          <span className={styles.triggerEmoji} aria-hidden="true">{emocion.emoji}</span>
          <span>{emocion.etiqueta}</span>
        </span>
      </div>
    )
  }

  function handleAbrir() {
    if (!abierto && wrapperRef.current) {
      const rect = wrapperRef.current.getBoundingClientRect()
      const espacioAbajo = window.innerHeight - rect.bottom - 64
      setPosicion(espacioAbajo < 160 ? 'arriba' : 'abajo')
    }
    setAbierto((v) => !v)
  }

  async function elegir(tipo: string) {
    setAbierto(false)
    try {
      const resultado = await toggleReactionMessage(messageId, tipo)
      if (resultado && 'reaccion' in resultado) onCambio(resultado.reaccion ?? null)
    } catch {
      // Si falla, se mantiene la reacción mostrada.
    }
  }

  return (
    <div className={styles.wrapper} ref={wrapperRef}>
      <button
        className={`${styles.trigger} ${styles.triggerSutil} ${reaccion ? styles.triggerActive : ''}`}
        onClick={handleAbrir}
        aria-expanded={abierto}
      >
        <span className={styles.triggerEmoji} aria-hidden="true">{emocion ? emocion.emoji : '🤍'}</span>
        <span>{emocion ? emocion.etiqueta : 'Reaccionar'}</span>
      </button>

      {abierto && (
        <div className={`${styles.panel} ${posicion === 'arriba' ? styles.panelArriba : ''}`}>
          <div className={styles.grid}>
            {EMOCIONES.map((e) => (
              <button
                key={e.clave}
                className={`${styles.opcion} ${reaccion === e.clave ? styles.opcionActiva : ''}`}
                onClick={() => elegir(e.clave)}
                aria-label={e.etiqueta}
                title={e.etiqueta}
              >
                <span className={styles.opcionEmoji}>{e.emoji}</span>
              </button>
            ))}
          </div>
          {reaccion && (
            <button className={styles.quitar} onClick={() => elegir(reaccion)}>
              Quitar mi reacción ({emocion?.etiqueta})
            </button>
          )}
        </div>
      )}
    </div>
  )
}