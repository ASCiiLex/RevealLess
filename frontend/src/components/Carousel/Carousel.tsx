import { useEffect, useState } from 'react'
import styles from './Carousel.module.css'
import Lomo, { type LomoObra } from './Lomo'
import { fetchCatalogoObras } from '../../api/obras'
import { useCatalogView } from '../../context/CatalogViewContext'

export default function Carousel() {
  const { view } = useCatalogView()
  const [obras, setObras] = useState<{ biblioteca: LomoObra[]; descubrir: LomoObra[] } | null>(
    null
  )

  useEffect(() => {
    fetchCatalogoObras()
      .then(setObras)
      .catch(() => setObras({ biblioteca: [], descubrir: [] }))
  }, [])

  if (!obras) {
    return null
  }

  const lista = obras[view]

  return (
    <div className={styles.wrapper}>
      {lista.length === 0 ? (
        <p className={styles.empty}>
          {view === 'biblioteca'
            ? 'Todavía no sigues ninguna obra. Explora en Descubrir.'
            : 'No hay más obras que descubrir por ahora.'}
        </p>
      ) : (
        <div className={styles.track}>
          {lista.map((obra) => (
            <Lomo key={obra.id} obra={obra} />
          ))}
        </div>
      )}
    </div>
  )
}