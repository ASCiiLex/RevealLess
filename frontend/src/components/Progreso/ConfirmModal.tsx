import styles from './ConfirmModal.module.css'
import botones from '../../styles/botones.module.css'

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
          <button className={botones.secundario} onClick={onCancel}>
            Cancelar
          </button>
          <button className={botones.primario} onClick={onConfirm}>
            Confirmar salto
          </button>
        </div>
      </div>
    </div>
  )
}