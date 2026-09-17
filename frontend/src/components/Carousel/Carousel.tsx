import { useEffect, useMemo, useRef, useState } from 'react'
import styles from './Carousel.module.css'
import Lomo, { type LomoObra } from './Lomo'
import CategoryChips from './CategoryChips'
import { fetchCatalogoObras } from '../../api/obras'
import { useCatalogView } from '../../context/CatalogViewContext'

export default function Carousel() {
  const { view, obraFiltro, setObraFiltro } = useCatalogView()
  const [obras, setObras] = useState<{ biblioteca: LomoObra[]; descubrir: LomoObra[] } | null>(
    null
  )
  const [categoriaActiva, setCategoriaActiva] = useState<string | null>(null)

  const trackRef = useRef<HTMLDivElement>(null)

  function recargarCatalogo() {
    fetchCatalogoObras()
      .then(setObras)
      .catch(() => setObras({ biblioteca: [], descubrir: [] }))
  }

  useEffect(() => {
    recargarCatalogo()
  }, [])

  useEffect(() => {
    setCategoriaActiva(null)
    setObraFiltro(null)
  }, [view, setObraFiltro])

  const listaCompleta = obras ? obras[view] : []

  const categoriasDisponibles = useMemo(() => {
    const set = new Set<string>()
    listaCompleta.forEach((obra) => obra.categorias?.forEach((cat) => set.add(cat)))
    return Array.from(set).sort()
  }, [listaCompleta])

  const listaFiltrada = categoriaActiva
    ? listaCompleta.filter((obra) => obra.categorias?.includes(categoriaActiva))
    : listaCompleta

  function handleSelectObra(obra: LomoObra) {
    setObraFiltro(obraFiltro === obra.id ? null : obra.id)
  }

  function desplazar(direccion: 'left' | 'right') {
    const track = trackRef.current
    if (!track) return

    const distancia = Math.max(track.clientWidth * 0.75, 300)

    track.scrollBy({
      left: direccion === 'right' ? distancia : -distancia,
      behavior: 'smooth',
    })
  }

  if (!obras) {
    return null
  }

  return (
    <div className={styles.wrapper}>
      <CategoryChips
        categorias={categoriasDisponibles}
        activa={categoriaActiva}
        onSelect={setCategoriaActiva}
      />

      <div className={styles.shelf} />

      {listaFiltrada.length === 0 ? (
        <div className={styles.shelfInterior}>
          <p className={styles.empty}>
            {view === 'biblioteca'
              ? 'Todavía no sigues ninguna obra en esta categoría.'
              : 'No hay obras que descubrir en esta categoría por ahora.'}
          </p>
        </div>
      ) : (
        <div className={styles.shelfInterior}>
          <div className={styles.carousel}>
            <button
              type="button"
              className={`${styles.arrow} ${styles.arrowLeft}`}
              onClick={() => desplazar('left')}
              aria-label="Desplazar obras hacia la izquierda"
            >
              ‹
            </button>

            <div ref={trackRef} className={styles.track}>
              {listaFiltrada.map((obra) => (
                <Lomo
                  key={obra.id}
                  obra={obra}
                  activa={obraFiltro === obra.id}
                  onSelect={handleSelectObra}
                  mostrarProgreso={view === 'biblioteca'}
                  onCambioSuscripcion={recargarCatalogo}
                />
              ))}
            </div>

            <button
              type="button"
              className={`${styles.arrow} ${styles.arrowRight}`}
              onClick={() => desplazar('right')}
              aria-label="Desplazar obras hacia la derecha"
            >
              ›
            </button>
          </div>
        </div>
      )}

      <div className={styles.shelf} />
    </div>
  )
}