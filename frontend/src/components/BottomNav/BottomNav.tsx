import styles from './BottomNav.module.css'
import { useOptionalCatalogView } from '../../context/CatalogViewContext'

export default function BottomNav() {
  const ctx = useOptionalCatalogView()

  function renderItem(target: 'biblioteca' | 'descubrir', label: string) {
    const active = ctx?.view === target

    if (ctx) {
      return (
        <button
          className={`${styles.item} ${active ? styles.itemActive : ''}`}
          onClick={() => ctx.setView(target)}
        >
          {label}
        </button>
      )
    }

    return (
      <a className={styles.item} href={`/feed/?view=${target}`}>
        {label}
      </a>
    )
  }

  return (
    <nav className={styles.nav}>
      {renderItem('biblioteca', 'Biblioteca')}

      <a className={styles.createButton} href="/posts/post/" aria-label="Crear publicación">
        +
      </a>

      {renderItem('descubrir', 'Descubrir')}
    </nav>
  )
}