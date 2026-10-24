import { useCallback, useEffect, useRef, useState } from 'react'
import styles from './CategoryChips.module.css'
import { esMovil } from '../../utils/dispositivo'

export type EstadoChip = 'o' | 'y'

interface Props {
  categorias: string[]
  estados: Record<string, EstadoChip>
  onCiclar: (categoria: string) => void
  onLimpiar: () => void
}

const DESCRIPCION: Record<EstadoChip, string> = {
  o: 'opcional (O)',
  y: 'obligatoria (Y)',
}

// Fracción del ancho visible que avanza cada flecha.
const PASO = 0.6
// En móvil basta el fundido como pista; en cualquier otro equipo, flechas aunque la pantalla sea táctil.
const CON_FLECHAS = !esMovil()

// Cada pulsación cicla: inactivo → O → Y → inactivo. "Todo" limpia el filtro.
export default function CategoryChips({ categorias, estados, onCiclar, onLimpiar }: Props) {
  const filaRef = useRef<HTMLDivElement>(null)
  const [hayIzquierda, setHayIzquierda] = useState(false)
  const [hayDerecha, setHayDerecha] = useState(false)

  const actualizar = useCallback(() => {
    const fila = filaRef.current
    if (!fila) return
    setHayIzquierda(fila.scrollLeft > 1)
    setHayDerecha(fila.scrollLeft + fila.clientWidth < fila.scrollWidth - 1)
  }, [])

  useEffect(() => {
    const fila = filaRef.current
    if (!fila) return
    fila.addEventListener('scroll', actualizar, { passive: true })
    const observador = new ResizeObserver(actualizar)
    observador.observe(fila)
    return () => {
      fila.removeEventListener('scroll', actualizar)
      observador.disconnect()
    }
  }, [actualizar, categorias.length])

  // La marca O/Y cambia el ancho de los chips sin cambiar el del contenedor.
  useEffect(actualizar, [actualizar, categorias, estados])

  function desplazar(sentido: 1 | -1) {
    const fila = filaRef.current
    if (fila) fila.scrollBy({ left: sentido * fila.clientWidth * PASO, behavior: 'smooth' })
  }

  if (categorias.length === 0) {
    return null
  }

  const hayFiltro = Object.keys(estados).length > 0
  const claseFundido = [hayIzquierda ? styles.fundidoIzquierda : '', hayDerecha ? styles.fundidoDerecha : '']
    .join(' ')

  return (
    <div className={styles.contenedor}>
      <div className={styles.marco}>
        {CON_FLECHAS && hayIzquierda && (
          <button
            type="button"
            className={`${styles.flecha} ${styles.flechaIzquierda}`}
            onClick={() => desplazar(-1)}
            aria-label="Ver categorías anteriores"
          >
            ‹
          </button>
        )}

        <div ref={filaRef} className={`${styles.wrapper} ${claseFundido}`}>
          <button
            type="button"
            className={`${styles.chip} ${hayFiltro ? '' : styles.chipY}`}
            onClick={onLimpiar}
            aria-pressed={!hayFiltro}
          >
            Todo
          </button>
          {categorias.map((cat) => {
            const estado = estados[cat]
            const clase = estado === 'y' ? styles.chipY : estado === 'o' ? styles.chipO : ''
            return (
              <button
                type="button"
                key={cat}
                className={`${styles.chip} ${clase}`}
                onClick={() => onCiclar(cat)}
                aria-label={estado ? `${cat}: ${DESCRIPCION[estado]}` : `${cat}: sin filtrar`}
                title={estado ? DESCRIPCION[estado] : undefined}
              >
                {estado && (
                  <span className={styles.marca} aria-hidden="true">
                    {estado === 'y' ? 'Y' : 'O'}
                  </span>
                )}
                {cat}
              </button>
            )
          })}
        </div>

        {CON_FLECHAS && hayDerecha && (
          <button
            type="button"
            className={`${styles.flecha} ${styles.flechaDerecha}`}
            onClick={() => desplazar(1)}
            aria-label="Ver más categorías"
          >
            ›
          </button>
        )}
      </div>
      {hayFiltro && (
        <p className={styles.ayuda}>
          O: cualquiera de ellas · Y: obligatoria · pulsa de nuevo un chip para cambiarlo
        </p>
      )}
    </div>
  )
}