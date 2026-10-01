import { useMemo, useRef, useState } from 'react'
import styles from './ProgresoSlider.module.css'
import type { UnidadNarrativa } from '../../api/progreso'

interface Props {
  unidades: UnidadNarrativa[]
  ordenActual: number | null
  pct: number | null
  onCommit: (unidadId: number) => void
}

const TECLAS_DESPLAZAMIENTO = ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End', 'PageUp', 'PageDown']

export default function ProgresoSlider({ unidades, ordenActual, pct, onCommit }: Props) {
  // Solo hojas: se avanza episodio a episodio (o capítulo), nunca por bloque.
  const hojas = useMemo(() => {
    const padres = new Set(unidades.map((u) => u.padre).filter((p): p is number => p !== null))
    return unidades.filter((u) => !padres.has(u.id)).sort((a, b) => a.orden_inicio - b.orden_inicio)
  }, [unidades])

  // Última hoja alcanzada; con progreso de bloque cae en la hoja anterior al bloque.
  const indiceActual = useMemo(() => {
    if (ordenActual === null) return -1
    let indice = -1
    hojas.forEach((h, i) => {
      if (h.orden_inicio <= ordenActual) indice = i
    })
    return indice
  }, [hojas, ordenActual])

  const [valor, setValor] = useState<number | null>(null)
  const [arrastrando, setArrastrando] = useState(false)
  const valorRef = useRef<number | null>(null)

  if (hojas.length === 0) return null

  const indice = valor ?? Math.max(indiceActual, 0)
  const hoja = hojas[indice]
  const posicion = hojas.length > 1 ? (indice / (hojas.length - 1)) * 100 : 0

  function cambiar(nuevo: number) {
    valorRef.current = nuevo
    setValor(nuevo)
    setArrastrando(true)
  }

  function confirmar() {
    setArrastrando(false)
    const elegido = valorRef.current
    if (elegido === null) return
    if (elegido === indiceActual) {
      valorRef.current = null
      setValor(null)
      return
    }
    // El valor se mantiene hasta que el padre resuelve (aplica o cancela y remonta).
    onCommit(hojas[elegido].id)
  }

  return (
    <div className={styles.contenedor}>
      <div className={styles.texto}>
        {ordenActual === null ? 'Desliza para marcar dónde vas' : `Tu progreso: ${pct ?? 0}%`}
      </div>
      <div className={styles.pista}>
        {arrastrando && (
          <div className={styles.popover} style={{ left: `${Math.min(Math.max(posicion, 15), 85)}%` }} role="status">
            {hoja.padre_etiqueta && <span className={styles.popoverPadre}>{hoja.padre_etiqueta}</span>}
            <span className={styles.popoverUnidad}>{hoja.etiqueta}</span>
          </div>
        )}
        <input
          type="range"
          className={styles.rango}
          min={0}
          max={hojas.length - 1}
          step={1}
          value={indice}
          aria-label="Progreso en la obra"
          aria-valuetext={hoja.etiqueta}
          onPointerDown={() => setArrastrando(true)}
          onChange={(e) => cambiar(Number(e.target.value))}
          onPointerUp={confirmar}
          onKeyUp={(e) => {
            if (TECLAS_DESPLAZAMIENTO.includes(e.key)) confirmar()
          }}
          onBlur={() => setArrastrando(false)}
        />
      </div>
    </div>
  )
}