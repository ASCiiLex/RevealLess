import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from 'react'
import styles from './BuscadorLocal.module.css'

export interface BuscadorItem {
  id: number
  label: string
}

interface Props {
  items: BuscadorItem[]
  value: number | null
  onChange: (id: number | null) => void
  placeholder: string
  emptyLabel?: string
  id?: string
}

/** Combobox con filtro local (sin llamadas a red): pensado para listas
 * ya cargadas en memoria (unidades narrativas, temas de una obra), que
 * en obras con cientos de capitulos eran inmanejables como <select>. */
export default function BuscadorLocal({ items, value, onChange, placeholder, emptyLabel, id }: Props) {
  const [abierto, setAbierto] = useState(false)
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const wrapperRef = useRef<HTMLDivElement>(null)

  const seleccionado = items.find((i) => i.id === value) ?? null

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

  const filtrados = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return items
    return items.filter((i) => i.label.toLowerCase().includes(q))
  }, [items, query])

  useEffect(() => {
    setActiveIndex(0)
  }, [query, abierto])

  function seleccionar(item: BuscadorItem) {
    onChange(item.id)
    setAbierto(false)
    setQuery('')
  }

  function limpiar() {
    onChange(null)
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
      setActiveIndex((i) => Math.min(i + 1, filtrados.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      const item = filtrados[activeIndex]
      if (item) seleccionar(item)
    } else if (e.key === 'Escape') {
      setAbierto(false)
      setQuery('')
    }
  }

  const mostrado = abierto ? query : (seleccionado?.label ?? '')

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
        {seleccionado && !abierto && (
          <button type="button" className={styles.clear} onClick={limpiar} aria-label="Quitar selección">×</button>
        )}
      </div>

      {abierto && (
        <div className={styles.dropdown}>
          {filtrados.length === 0 ? (
            <p className={styles.empty}>Sin resultados.</p>
          ) : (
            filtrados.map((item, i) => (
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