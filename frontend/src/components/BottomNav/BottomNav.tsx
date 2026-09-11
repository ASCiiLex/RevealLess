import styles from './BottomNav.module.css'
import { useCatalogView } from '../../context/CatalogViewContext'

export default function BottomNav() {
  const { view, setView } = useCatalogView()

  return (
    <nav className={styles.nav}>
      <button
        className={`${styles.item} ${view === 'biblioteca' ? styles.itemActive : ''}`}
        onClick={() => setView('biblioteca')}
      >
        Biblioteca
      </button>

      <a className={styles.createButton} href="/narrative/publicar/" aria-label="Crear publicación">
        +
      </a>

      <button
        className={`${styles.item} ${view === 'descubrir' ? styles.itemActive : ''}`}
        onClick={() => setView('descubrir')}
      >
        Descubrir
      </button>
    </nav>
  )
}