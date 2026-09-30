import { useEffect, useMemo, useRef, useState } from 'react'
import styles from './Carousel.module.css'
import Lomo, { type LomoObra } from './Lomo'
import CategoryChips, { type EstadoChip } from './CategoryChips'
import { fetchCatalogoObras } from '../../api/obras'
import { useCatalogView } from '../../context/CatalogViewContext'

const CHIP_TEMAS = 'Temas'

type Filtros = Record<string, EstadoChip>

const SIGUIENTE: Record<'-' | EstadoChip, EstadoChip | null> = { '-': 'o', o: 'y', y: null }

function tiene(obra: LomoObra, categoria: string) {
  if (categoria === CHIP_TEMAS) return Boolean(obra.es_tema)
  if (obra.es_tema) return false
  return obra.categorias?.includes(categoria) ?? false
}

// Todas las Y obligatorias y, si hay alguna O, al menos una de ellas.
function coincide(obra: LomoObra, filtros: Filtros) {
  const entradas = Object.entries(filtros)
  const obligatorias = entradas.filter(([, e]) => e === 'y').map(([c]) => c)
  const opcionales = entradas.filter(([, e]) => e === 'o').map(([c]) => c)
  return (
    obligatorias.every((c) => tiene(obra, c)) &&
    (opcionales.length === 0 || opcionales.some((c) => tiene(obra, c)))
  )
}

export default function Carousel() {
  const { view, obraFiltro, setObraFiltro } = useCatalogView()
  const [obras, setObras] = useState<{ biblioteca: LomoObra[]; descubrir: LomoObra[] } | null>(
    null
  )
  const [filtros, setFiltros] = useState<Filtros>({})

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
    setFiltros({})
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

  const hayFiltro = Object.keys(filtros).length > 0
  const listaFiltrada = hayFiltro
    ? listaCompleta.filter((obra) => coincide(obra, filtros))
    : listaCompleta

  function ciclarCategoria(categoria: string) {
    setFiltros((actuales) => {
      const siguiente = SIGUIENTE[actuales[categoria] ?? '-']
      const { [categoria]: _, ...resto } = actuales
      return siguiente ? { ...resto, [categoria]: siguiente } : resto
    })
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
        estados={filtros}
        onCiclar={ciclarCategoria}
        onLimpiar={() => setFiltros({})}
      />

      <div className={styles.shelf} />

      {listaFiltrada.length === 0 ? (
        <div className={styles.shelfInterior}>
          <p className={styles.empty}>
            {view === 'biblioteca'
              ? 'Todavía no sigues ninguna obra con esta combinación de categorías.'
              : 'No hay obras que descubrir con esta combinación de categorías.'}
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