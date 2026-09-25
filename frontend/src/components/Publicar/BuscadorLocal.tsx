import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import styles from './BuscadorLocal.module.css'

export interface BuscadorItem {
  id: number
  label: string
}

interface Props {
  value: number | null
  valueLabel?: string | null
  onChange: (id: number | null, label: string | null) => void
  placeholder: string
  emptyLabel?: string
  id?: string
  buscar: (q: string) => Promise<BuscadorItem[]>
}

/** Combobox con busqueda en servidor (con debounce), no en memoria:
 * pensado para listas que pueden ser enormes (una obra con miles de
 * unidades narrativas importadas) -- cargarlas todas de golpe en el
 * frontend tardaba varios segundos solo en montar el componente. */
export default function BuscadorLocal({ value, valueLabel, onChange, placeholder, emptyLabel, id, buscar }: Props) {
  const [abierto, setAbierto] = useState(false)
  const [query, setQuery] = useState('')
  const [resultados, setResultados] = useState<BuscadorItem[]>([])
  const [activeIndex, setActiveIndex] = useState(0)
  const [buscando, setBuscando] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setAbierto(false)
        setQuery('')
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    if (!abierto) return
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => {
      setBuscando(true)
      buscar(query.trim())
        .then(setResultados)
        .finally(() => setBuscando(false))
    }, 250)
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [query, abierto, buscar])

  useEffect(() => {
    setActiveIndex(0)
  }, [resultados])

  function seleccionar(item: BuscadorItem) {
    onChange(item.id, item.label)
    setAbierto(false)
    setQuery('')
  }

  function limpiar() {
    onChange(null, null)
    setAbierto(false)
    setQuery('')
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (!abierto) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        e.preventDefault()
        setAbierto(true)
      }
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex((i) => Math.min(i + 1, resultados.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      const item = resultados[activeIndex]
      if (item) seleccionar(item)
    } else if (e.key === 'Escape') {
      setAbierto(false)
      setQuery('')
    }
  }

  const mostrado = abierto ? query : (valueLabel ?? '')

  return (
    <div className={styles.wrapper} ref={wrapperRef}>
      <div className={styles.inputRow}>
        <input
          id={id}
          className={styles.input}
          type="text"
          value={mostrado}
          placeholder={emptyLabel ?? placeholder}
          onFocus={() => setAbierto(true)}
          onChange={(e) => { setQuery(e.target.value); setAbierto(true) }}
          onKeyDown={handleKeyDown}
          autoComplete="off"
        />
        {value !== null && !abierto && (
          <button type="button" className={styles.clear} onClick={limpiar} aria-label="Quitar selección">×</button>
        )}
      </div>

      {abierto && (
        <div className={styles.dropdown}>
          {buscando ? (
            <p className={styles.empty}>Buscando...</p>
          ) : resultados.length === 0 ? (
            <p className={styles.empty}>Sin resultados.</p>
          ) : (
            resultados.map((item, i) => (
              <button
                key={item.id}
                type="button"
                className={`${styles.option} ${i === activeIndex ? styles.optionActive : ''}`}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => seleccionar(item)}
              >
                {item.label}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}