import { useEffect, useState } from 'react'
import styles from './MobileSearchOverlay.module.css'
import SearchResults from './SearchResults'
import { buscar, type ResultadoBusqueda } from '../../api/buscar'

interface Props {
  onClose: () => void
}

export default function MobileSearchOverlay({ onClose }: Props) {
  const [query, setQuery] = useState('')
  const [resultado, setResultado] = useState<ResultadoBusqueda | null>(null)

  useEffect(() => {
    if (query.trim().length < 2) {
      setResultado(null)
      return
    }
    const id = setTimeout(() => {
      buscar(query.trim()).then(setResultado)
    }, 300)
    return () => clearTimeout(id)
  }, [query])

  return (
    <div className={`container ${styles.overlay}`}>
      <div className={styles.row}>
        <input
          className={styles.input}
          type="search"
          placeholder="Buscar obras, temas..."
          aria-label="Buscar"
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button className={styles.close} onClick={onClose} aria-label="Cerrar búsqueda">
          ✕
        </button>
      </div>
      {resultado && <SearchResults resultado={resultado} />}
    </div>
  )
}