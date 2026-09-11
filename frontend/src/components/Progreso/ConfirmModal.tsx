import styles from './ConfirmModal.module.css'

interface Props {
  mensaje: string
  onConfirm: () => void
  onCancel: () => void
}

export default function ConfirmModal({ mensaje, onConfirm, onCancel }: Props) {
  return (
    <div className={styles.overlay} onClick={onCancel}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <p className={styles.text}>{mensaje}</p>
        <div className={styles.actions}>
          <button className={`${styles.button} ${styles.cancel}`} onClick={onCancel}>
            Cancelar
          </button>
          <button className={`${styles.button} ${styles.confirm}`} onClick={onConfirm}>
            Confirmar salto
          </button>
        </div>
      </div>
    </div>
  )
}