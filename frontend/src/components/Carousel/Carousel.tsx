import { useEffect, useMemo, useRef, useState } from 'react'
import styles from './Carousel.module.css'
import Lomo, { type LomoObra } from './Lomo'
import CategoryChips, { type EstadoChip } from './CategoryChips'
import { fetchCatalogoObras } from '../../api/obras'
import { useCatalogView } from '../../context/CatalogViewContext'
import { esMovil } from '../../utils/dispositivo'

const CHIP_TEMAS = 'Temas'
const CHIP_PERSONAJES = 'Personajes'
// En móvil se desliza con el dedo; en cualquier otro equipo, flechas aunque la pantalla sea táctil.
const CON_FLECHAS = !esMovil()

type Filtros = Record<string, EstadoChip>

const SIGUIENTE: Record<'-' | EstadoChip, EstadoChip | null> = { '-': 'o', o: 'y', y: null }

interface Props {
  // Seguir o dejar de seguir cambia qué posts entran en el feed.
  onCambioSuscripcion?: () => void
}

function tiene(lomo: LomoObra, categoria: string) {
  if (categoria === CHIP_TEMAS) return Boolean(lomo.es_tema)
  if (categoria === CHIP_PERSONAJES) return Boolean(lomo.es_personaje)
  if (lomo.es_tema || lomo.es_personaje) return false
  return lomo.categorias?.includes(categoria) ?? false
}

// Todas las Y obligatorias y, si hay alguna O, al menos una de ellas.
function coincide(lomo: LomoObra, filtros: Filtros) {
  const entradas = Object.entries(filtros)
  const obligatorias = entradas.filter(([, e]) => e === 'y').map(([c]) => c)
  const opcionales = entradas.filter(([, e]) => e === 'o').map(([c]) => c)
  return (
    obligatorias.every((c) => tiene(lomo, c)) &&
    (opcionales.length === 0 || opcionales.some((c) => tiene(lomo, c)))
  )
}

export default function Carousel({ onCambioSuscripcion }: Props) {
  const {
    view,
    obraFiltro,
    setObraFiltro,
    temaFiltro,
    setTemaFiltro,
    personajeFiltro,
    setPersonajeFiltro,
    setFiltroSilenciado,
  } = useCatalogView()
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

  function handleCambioSuscripcion() {
    recargarCatalogo()
    onCambioSuscripcion?.()
  }

  useEffect(() => {
    recargarCatalogo()
  }, [])

  useEffect(() => {
    setFiltros({})
    setObraFiltro(null)
    setTemaFiltro(null)
    setPersonajeFiltro(null)
    setFiltroSilenciado(false)
  }, [view, setObraFiltro, setTemaFiltro, setPersonajeFiltro, setFiltroSilenciado])

  const listaCompleta = obras ? obras[view] : []

  const categoriasDisponibles = useMemo(() => {
    const set = new Set<string>()
    let hayTemas = false
    let hayPersonajes = false
    listaCompleta.forEach((lomo) => {
      if (lomo.es_tema) {
        hayTemas = true
        return
      }
      if (lomo.es_personaje) {
        hayPersonajes = true
        return
      }
      lomo.categorias?.forEach((cat) => set.add(cat))
    })
    const categorias = Array.from(set).sort()
    if (hayTemas) categorias.push(CHIP_TEMAS)
    if (hayPersonajes) categorias.push(CHIP_PERSONAJES)
    return categorias
  }, [listaCompleta])

  const hayFiltro = Object.keys(filtros).length > 0
  const listaFiltrada = hayFiltro
    ? listaCompleta.filter((lomo) => coincide(lomo, filtros))
    : listaCompleta

  function ciclarCategoria(categoria: string) {
    setFiltros((actuales) => {
      const siguiente = SIGUIENTE[actuales[categoria] ?? '-']
      const { [categoria]: _, ...resto } = actuales
      return siguiente ? { ...resto, [categoria]: siguiente } : resto
    })
  }

  function estaActivo(lomo: LomoObra) {
    if (lomo.es_personaje) return personajeFiltro === lomo.personaje_id
    if (lomo.es_tema) return temaFiltro === lomo.tema_id
    return obraFiltro === lomo.id
  }

  // Cada tipo filtra por su id real. Pulsar de nuevo el mismo lomo quita el filtro.
  function handleSelectObra(lomo: LomoObra) {
    const seleccionar = !estaActivo(lomo)
    const esObra = !lomo.es_tema && !lomo.es_personaje
    setObraFiltro(seleccionar && esObra ? lomo.id : null)
    setTemaFiltro(seleccionar && lomo.es_tema ? lomo.tema_id ?? null : null)
    setPersonajeFiltro(seleccionar && lomo.es_personaje ? lomo.personaje_id ?? null : null)
    setFiltroSilenciado(seleccionar && Boolean(lomo.silenciada))
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
            {CON_FLECHAS && (
              <button
                type="button"
                className={`${styles.arrow} ${styles.arrowLeft}`}
                onClick={() => desplazar('left')}
                aria-label="Desplazar obras hacia la izquierda"
              >
                ‹
              </button>
            )}

            <div ref={trackRef} className={`${styles.track} ${CON_FLECHAS ? styles.conFlechas : ''}`}>
              {listaFiltrada.map((lomo) => (
                <Lomo
                  key={lomo.clave}
                  obra={lomo}
                  activa={estaActivo(lomo)}
                  onSelect={handleSelectObra}
                  mostrarProgreso={view === 'biblioteca'}
                  onCambioSuscripcion={handleCambioSuscripcion}
                />
              ))}
            </div>

            {CON_FLECHAS && (
              <button
                type="button"
                className={`${styles.arrow} ${styles.arrowRight}`}
                onClick={() => desplazar('right')}
                aria-label="Desplazar obras hacia la derecha"
              >
                ›
              </button>
            )}
          </div>
        </div>
      )}

      <div className={styles.shelf} />
    </div>
  )
}