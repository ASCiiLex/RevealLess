import { useEffect, useMemo, useRef, useState } from 'react'
import styles from './Carousel.module.css'
import Lomo, { type LomoObra } from './Lomo'
import CategoryChips from './CategoryChips'
import { fetchCatalogoObras } from '../../api/obras'
import { useCatalogView } from '../../context/CatalogViewContext'

const CHIP_TEMAS = 'Temas'

// OR: una obra entra si coincide con cualquiera de los chips activos.
function coincide(obra: LomoObra, activas: string[]) {
  if (obra.es_tema) return activas.includes(CHIP_TEMAS)
  return obra.categorias?.some((c) => activas.includes(c)) ?? false
}

export default function Carousel() {
  const { view, obraFiltro, setObraFiltro } = useCatalogView()
  const [obras, setObras] = useState<{ biblioteca: LomoObra[]; descubrir: LomoObra[] } | null>(
    null
  )
  const [categoriasActivas, setCategoriasActivas] = useState<string[]>([])

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
    setCategoriasActivas([])
    setObraFiltro(null)
  }, [view, setObraFiltro])

  const listaCompleta = obras ? obras[view] : []

  const categoriasDisponibles = useMemo(() => {
    const set = new Set<string>()
    let hayTemas = false
    listaCompleta.forEach((obra) => {
      if (obra.es_tema) {
        hayTemas = true
        return
      }
      obra.categorias?.forEach((cat) => set.add(cat))
    })
    const categorias = Array.from(set).sort()
    if (hayTemas) {
      categorias.push(CHIP_TEMAS)
    }
    return categorias
  }, [listaCompleta])

  const listaFiltrada =
    categoriasActivas.length === 0
      ? listaCompleta
      : listaCompleta.filter((obra) => coincide(obra, categoriasActivas))

  function toggleCategoria(categoria: string) {
    setCategoriasActivas((actuales) =>
      actuales.includes(categoria) ? actuales.filter((c) => c !== categoria) : [...actuales, categoria]
    )
  }

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
        activas={categoriasActivas}
        onToggle={toggleCategoria}
        onLimpiar={() => setCategoriasActivas([])}
      />

      <div className={styles.shelf} />

      {listaFiltrada.length === 0 ? (
        <div className={styles.shelfInterior}>
          <p className={styles.empty}>
            {view === 'biblioteca'
              ? 'Todavía no sigues ninguna obra en estas categorías.'
              : 'No hay obras que descubrir en estas categorías por ahora.'}
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