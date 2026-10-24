import { useId, useMemo, useRef, useState } from 'react'
import styles from './ProgresoSlider.module.css'
import type { UnidadNarrativa } from '../../api/progreso'
import { TIPO_PREVIO, hojasDe, tipoPrincipal } from '../../utils/progresoPct'

interface Props {
  unidades: UnidadNarrativa[]
  ordenActual: number | null
  pct: number | null
  onCommit: (unidadId: number) => void
}

const TECLAS_DESPLAZAMIENTO = ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End', 'PageUp', 'PageDown']
const MAX_COINCIDENCIAS = 5

// Vacío o inválido cuenta como 1.
function cantidad(texto: string) {
  const n = parseInt(texto, 10)
  return Number.isNaN(n) || n < 1 ? 1 : n
}

export default function ProgresoSlider({ unidades, ordenActual, pct, onCommit }: Props) {
  // Solo hojas: se avanza episodio a episodio (o capítulo), nunca por bloque.
  const hojas = useMemo(() => hojasDe(unidades), [unidades])

  // Solo se numeran las hojas del tipo principal (misma regla que el porcentaje):
  // previos y películas intercaladas no cuentan. Un previo inicial es la posición 0.
  const numeros = useMemo(() => {
    const principal = tipoPrincipal(hojas)
    let n = 0
    return hojas.map((h, i) => (h.tipo === principal ? ++n : i === 0 && h.tipo === TIPO_PREVIO ? 0 : null))
  }, [hojas])

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
  const [texto, setTexto] = useState('')
  const [enfocado, setEnfocado] = useState(false)
  const [activa, setActiva] = useState(0)
  const [restar, setRestar] = useState('')
  const [sumar, setSumar] = useState('')
  const valorRef = useRef<number | null>(null)
  const idLista = useId()

  if (hojas.length === 0) return null

  const ultimo = hojas.length - 1
  const total = numeros.reduce<number>((max, n) => Math.max(max, n ?? 0), 0)
  const minimo = numeros[0] === 0 ? 0 : 1
  const indice = valor ?? Math.max(indiceActual, 0)
  const hoja = hojas[indice]
  const posicion = hojas.length > 1 ? (indice / ultimo) * 100 : 0

  // En una hoja sin número (previo o película intercalados) se muestra el de la última numerada.
  function numeroAlcanzado(i: number) {
    for (let k = i; k >= 0; k--) {
      const n = numeros[k]
      if (n !== null) return n
    }
    return 0
  }

  // Opciones del campo numérico: primero el destino por número (Enter),
  // después unidades cuyo nombre lleva ese número como palabra completa.
  const numero = parseInt(texto, 10)
  const opciones: number[] = []
  if (!Number.isNaN(numero)) {
    const destino = numeros.indexOf(Math.min(Math.max(numero, minimo), total))
    if (destino >= 0) opciones.push(destino)
    const patron = new RegExp(`\\b${numero}\\b`)
    for (let i = 0; i < hojas.length && opciones.length <= MAX_COINCIDENCIAS; i++) {
      if (i !== destino && patron.test(hojas[i].etiqueta)) opciones.push(i)
    }
  }

  function cambiar(nuevo: number) {
    valorRef.current = nuevo
    setValor(nuevo)
    setArrastrando(true)
  }

  // Punto único de confirmación para slider, botones y campos numéricos.
  function aplicar(elegido: number) {
    if (elegido === indiceActual) {
      valorRef.current = null
      setValor(null)
      return
    }
    valorRef.current = elegido
    setValor(elegido)
    // El valor se mantiene hasta que el padre resuelve (aplica o cancela y remonta).
    onCommit(hojas[elegido].id)
  }

  function confirmar() {
    setArrastrando(false)
    if (valorRef.current !== null) aplicar(valorRef.current)
  }

  function desplazar(paso: number) {
    // Sin progreso, «+N» parte de antes de la primera hoja.
    const base = indiceActual < 0 ? (paso > 0 ? -1 : 0) : indiceActual
    aplicar(Math.min(Math.max(base + paso, 0), ultimo))
  }

  function elegirOpcion(i: number) {
    setTexto('')
    setActiva(0)
    aplicar(i)
  }

  function alPulsarEnter(accion: () => void) {
    return (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        e.preventDefault()
        accion()
      }
    }
  }

  function teclaNumero(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Escape') {
      setTexto('')
      setActiva(0)
    } else if (e.key === 'ArrowDown' && opciones.length > 1) {
      e.preventDefault()
      setActiva((a) => Math.min(a + 1, opciones.length - 1))
    } else if (e.key === 'ArrowUp' && opciones.length > 1) {
      e.preventDefault()
      setActiva((a) => Math.max(a - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      const elegida = opciones[activa] ?? opciones[0]
      if (elegida !== undefined) elegirOpcion(elegida)
    }
  }

  function renderOpcion(i: number, k: number) {
    const unidad = hojas[i]
    return (
      <button
        key={i}
        type="button"
        role="option"
        aria-selected={k === activa}
        className={`${styles.sugerencia} ${k === activa ? styles.sugerenciaActiva : ''}`}
        // mousedown sin foco: el input no se cierra antes del click.
        onMouseDown={(e) => e.preventDefault()}
        onMouseEnter={() => setActiva(k)}
        onClick={() => elegirOpcion(i)}
      >
        {k === 0 && <span className={styles.sugerenciaPosicion}>Posición {numeros[i]}</span>}
        {unidad.padre_etiqueta && <span className={styles.sugerenciaPadre}>{unidad.padre_etiqueta}</span>}
        <span className={styles.sugerenciaUnidad}>{unidad.etiqueta}</span>
      </button>
    )
  }

  const nRestar = cantidad(restar)
  const nSumar = cantidad(sumar)

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
          max={ultimo}
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

      <div className={styles.stepper}>
        <div className={styles.grupo}>
          <button
            type="button"
            className={styles.paso}
            onClick={() => desplazar(-nRestar)}
            disabled={indiceActual <= 0}
            aria-label={`Retroceder ${nRestar}`}
          >
            −
          </button>
          <input
            type="number"
            inputMode="numeric"
            className={`${styles.campo} ${styles.cantidad}`}
            min={1}
            value={restar}
            placeholder="1"
            aria-label="Cantidad a retroceder"
            onChange={(e) => setRestar(e.target.value)}
            onKeyDown={alPulsarEnter(() => indiceActual > 0 && desplazar(-nRestar))}
          />
        </div>

        <div className={`${styles.grupo} ${styles.grupoNumero}`}>
          <input
            type="number"
            inputMode="numeric"
            className={`${styles.campo} ${styles.numero}`}
            min={minimo}
            max={total}
            value={texto}
            placeholder={indiceActual >= 0 ? String(numeroAlcanzado(indiceActual)) : '—'}
            aria-label={
              minimo === 0
                ? `Ir a la unidad número (0 = previo al estreno, 1 a ${total})`
                : `Ir a la unidad número (1 a ${total})`
            }
            aria-controls={idLista}
            aria-expanded={enfocado && opciones.length > 0}
            onChange={(e) => {
              setTexto(e.target.value)
              setActiva(0)
            }}
            onFocus={() => setEnfocado(true)}
            onBlur={() => setEnfocado(false)}
            onKeyDown={teclaNumero}
          />
          <span className={styles.total}>/ {total}</span>

          {enfocado && opciones.length > 0 && (
            <div id={idLista} className={styles.sugerencias} role="listbox">
              {renderOpcion(opciones[0], 0)}
              {opciones.length > 1 && (
                <>
                  <div className={styles.sugerenciasTitulo}>También con «{numero}» en el nombre</div>
                  {opciones.slice(1).map((i, k) => renderOpcion(i, k + 1))}
                </>
              )}
            </div>
          )}
        </div>

        <div className={styles.grupo}>
          <input
            type="number"
            inputMode="numeric"
            className={`${styles.campo} ${styles.cantidad}`}
            min={1}
            value={sumar}
            placeholder="1"
            aria-label="Cantidad a avanzar"
            onChange={(e) => setSumar(e.target.value)}
            onKeyDown={alPulsarEnter(() => indiceActual < ultimo && desplazar(nSumar))}
          />
          <button
            type="button"
            className={styles.paso}
            onClick={() => desplazar(nSumar)}
            disabled={indiceActual >= ultimo}
            aria-label={`Avanzar ${nSumar}`}
          >
            +
          </button>
        </div>
      </div>
    </div>
  )
}