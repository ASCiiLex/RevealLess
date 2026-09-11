import styles from './Tabs.module.css'
import { useCatalogView } from '../../context/CatalogViewContext'

export default function Tabs() {
  const { view, setView } = useCatalogView()

  return (
    <div className={styles.tabs} role="tablist">
      <button
        className={`${styles.tab} ${view === 'biblioteca' ? styles.tabActive : ''}`}
        onClick={() => setView('biblioteca')}
        role="tab"
        aria-selected={view === 'biblioteca'}
      >
        Biblioteca
      </button>
      <button
        className={`${styles.tab} ${view === 'descubrir' ? styles.tabActive : ''}`}
        onClick={() => setView('descubrir')}
        role="tab"
        aria-selected={view === 'descubrir'}
      >
        Descubrir
      </button>
    </div>
  )
}