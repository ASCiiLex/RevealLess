import styles from './MobileSearchOverlay.module.css'

interface Props {
  onClose: () => void
}

export default function MobileSearchOverlay({ onClose }: Props) {
  return (
    <div className={`container ${styles.overlay}`}>
      <input
        className={styles.input}
        type="search"
        placeholder="Buscar obras, temas..."
        aria-label="Buscar"
        autoFocus
      />
      <button className={styles.close} onClick={onClose} aria-label="Cerrar búsqueda">
        ✕
      </button>
    </div>
  )
}