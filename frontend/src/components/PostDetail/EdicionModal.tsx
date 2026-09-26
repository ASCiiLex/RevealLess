import type { ReactNode } from 'react'
import styles from './EdicionModal.module.css'

interface Props {
  titulo: string
  error: string | null
  aviso: string | null
  onConfirmarAviso: () => void
  guardando: boolean
  puedeGuardar: boolean
  onGuardar: () => void
  onCancelar: () => void
  children: ReactNode
}

export default function EdicionModal({
  titulo, error, aviso, onConfirmarAviso, guardando, puedeGuardar, onGuardar, onCancelar, children,
}: Props) {
  return (
    <div className={styles.overlay} onClick={onCancelar}>
      <div
        className={styles.panel}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
      >
        <h2 className={styles.title}>{titulo}</h2>

        <div className={styles.form}>
          {error && <p className={styles.error}>{error}</p>}

          {aviso && (
            <div className={styles.warningBox}>
              {aviso}
              <br />
              <button className={styles.confirmLink} onClick={onConfirmarAviso}>
                Entiendo, continuar de todas formas
              </button>
            </div>
          )}

          {children}

          <div className={styles.actions}>
            <button className={`${styles.button} ${styles.cancel}`} onClick={onCancelar}>
              Cancelar
            </button>
            <button
              className={`${styles.button} ${styles.confirm}`}
              onClick={onGuardar}
              disabled={guardando || !puedeGuardar}
            >
              {guardando ? 'Guardando...' : 'Guardar cambios'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}