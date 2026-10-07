import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import styles from './SelectorParteTema.module.css'
import { buscarUnidades, type UnidadBuscada } from '../../api/suscripciones'

export interface Seleccion {
  id: number | null
  label: string | null
}

interface TemaPlano {
  id: number
  nombre: string
}

interface Props {
  id: string
  obraSlug: string | null
  temas: TemaPlano[]
  parte: Seleccion
  tema: Seleccion
  temaPropuesto: string | null
  onParte: (seleccion: Seleccion) => void
  onTema: (seleccion: Seleccion) => void
  onProponerTema: (nombre: string | null) => void
}

type Opcion =
  | { tipo: 'parte'; id: number; label: string; detalle: string | null }
  | { tipo: 'tema'; id: number; label: string }
  | { tipo: 'proponer'; label: string }

const MAX_TEMAS = 8
const RETARDO_BUSQUEDA_MS = 250
const TITULO_GRUPO = { parte: 'Partes', tema: 'Temas', proponer: null }

function normalizar(texto: string) {
  return texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim()
}

// Un solo campo para «de qué habla»: una parte, un tema (existente o propuesto) o ambos.
export default function SelectorParteTema({
  id, obraSlug, temas, parte, tema, temaPropuesto, onParte, onTema, onProponerTema,
}: Props) {
  const [abierto, setAbierto] = useState(false)
  const [query, setQuery] = useState('')
  const [partes, setPartes] = useState<UnidadBuscada[]>([])
  const [buscando, setBuscando] = useState(false)
  const [activa, setActiva] = useState(0)
  const wrapperRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function fuera(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setAbierto(false)
        setQuery('')
      }
    }
    document.addEventListener('mousedown', fuera)
    return () => document.removeEventListener('mousedown', fuera)
  }, [])

  useEffect(() => {
    if (!abierto || !obraSlug) return
    const temporizador = setTimeout(() => {
      setBuscando(true)
      buscarUnidades(obraSlug, query.trim())
        .then(setPartes)
        .finally(() => setBuscando(false))
    }, RETARDO_BUSQUEDA_MS)
    return () => clearTimeout(temporizador)
  }, [query, abierto, obraSlug])

  const q = normalizar(query)
  const temasFiltrados = temas.filter((t) => !q || normalizar(t.nombre).includes(q)).slice(0, MAX_TEMAS)
  const hayExacto = temas.some((t) => normalizar(t.nombre) === q)
  const opciones: Opcion[] = [
    ...partes.map((p) => ({ tipo: 'parte' as const, id: p.id, label: p.label, detalle: p.detalle })),
    ...temasFiltrados.map((t) => ({ tipo: 'tema' as const, id: t.id, label: t.nombre })),
    ...(q && !hayExacto ? [{ tipo: 'proponer' as const, label: query.trim() }] : []),
  ]

  useEffect(() => {
    setActiva(0)
  }, [query, partes.length])

  function elegir(opcion: Opcion) {
    if (opcion.tipo === 'parte') onParte({ id: opcion.id, label: opcion.label })
    else if (opcion.tipo === 'tema') onTema({ id: opcion.id, label: opcion.label })
    else onProponerTema(opcion.label)
    setQuery('')
    setAbierto(false)
  }

  function teclado(e: KeyboardEvent<HTMLInputElement>) {
    if (!abierto) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setAbierto(true)
      }
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiva((i) => Math.min(i + 1, opciones.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiva((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      const opcion = opciones[activa]
      if (opcion) elegir(opcion)
    } else if (e.key === 'Escape') {
      setAbierto(false)
      setQuery('')
    }
  }

  const etiquetaTema = temaPropuesto ? `${temaPropuesto} (propuesta)` : tema.label

  return (
    <div className={styles.wrapper} ref={wrapperRef}>
      {(parte.id || tema.id || temaPropuesto) && (
        <div className={styles.chips}>
          {parte.id && (
            <span className={styles.chip}>
              <span aria-hidden="true">📖</span> {parte.label}
              <button
                type="button"
                className={styles.chipQuitar}
                onClick={() => onParte({ id: null, label: null })}
                aria-label="Quitar la parte"
              >
                ×
              </button>
            </span>
          )}
          {(tema.id || temaPropuesto) && (
            <span className={`${styles.chip} ${temaPropuesto ? styles.chipPropuesto : ''}`}>
              #{etiquetaTema}
              <button
                type="button"
                className={styles.chipQuitar}
                onClick={() => (temaPropuesto ? onProponerTema(null) : onTema({ id: null, label: null }))}
                aria-label="Quitar el tema"
              >
                ×
              </button>
            </span>
          )}
        </div>
      )}

      <input
        id={id}
        className={styles.input}
        type="text"
        value={query}
        placeholder="Busca una parte (episodio, capítulo…) o un tema"
        onFocus={() => setAbierto(true)}
        onChange={(e) => {
          setQuery(e.target.value)
          setAbierto(true)
        }}
        onKeyDown={teclado}
        autoComplete="off"
      />

      {abierto && (
        <div className={styles.dropdown}>
          {opciones.map((opcion, i) => {
            const titulo = i === 0 || opciones[i - 1].tipo !== opcion.tipo ? TITULO_GRUPO[opcion.tipo] : null
            return (
              <div key={`${opcion.tipo}-${'id' in opcion ? opcion.id : opcion.label}`}>
                {titulo && <p className={styles.grupo}>{titulo}</p>}
                <button
                  type="button"
                  className={`${styles.option} ${opcion.tipo === 'proponer' ? styles.optionProponer : ''} ${
                    i === activa ? styles.optionActive : ''
                  }`}
                  onMouseDown={(e) => e.preventDefault()}
                  onMouseEnter={() => setActiva(i)}
                  onClick={() => elegir(opcion)}
                >
                  {opcion.tipo === 'parte' && (
                    <>
                      {opcion.label}
                      {opcion.detalle && <span className={styles.detalle}>{opcion.detalle}</span>}
                    </>
                  )}
                  {opcion.tipo === 'tema' && `#${opcion.label}`}
                  {opcion.tipo === 'proponer' && `Proponer «${opcion.label}» como tema nuevo`}
                </button>
              </div>
            )
          })}
          {opciones.length === 0 && (
            <p className={styles.empty}>{buscando ? 'Buscando...' : 'Sin resultados.'}</p>
          )}
        </div>
      )}
    </div>
  )
}