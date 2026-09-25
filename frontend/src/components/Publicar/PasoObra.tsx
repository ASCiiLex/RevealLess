import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from 'react'
import styles from './PasoObra.module.css'
import { buscar } from '../../api/buscar'
import type { TemaBusqueda } from '../../api/buscar'
import type { LomoObra } from '../Carousel/Lomo'

interface ObraElegida {
  slug: string
  titulo: string
}

interface Props {
  onElegirObra: (obra: ObraElegida) => void
  onElegirTema: (tema: TemaBusqueda) => void
}

type ResultadoCombinado =
  | { tipo: 'obra'; item: LomoObra }
  | { tipo: 'tema'; item: TemaBusqueda }

export default function PasoObra({ onElegirObra, onElegirTema }: Props) {
  const [query, setQuery] = useState('')
  const [obras, setObras] = useState<LomoObra[]>([])
  const [temas, setTemas] = useState<TemaBusqueda[]>([])
  const [buscando, setBuscando] = useState(false)
  const [activeIndex, setActiveIndex] = useState(0)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)

    if (query.trim().length < 2) {
      setObras([])
      setTemas([])
      return
    }

    timeoutRef.current = setTimeout(() => {
      setBuscando(true)
      buscar(query.trim())
        .then((resultado) => {
          setObras(resultado.obras)
          setTemas(resultado.temas)
        })
        .finally(() => setBuscando(false))
    }, 300)

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [query])

  const combinados: ResultadoCombinado[] = useMemo(
    () => [
      ...obras.map((item) => ({ tipo: 'obra' as const, item })),
      ...temas.map((item) => ({ tipo: 'tema' as const, item })),
    ],
    [obras, temas]
  )

  useEffect(() => {
    setActiveIndex(0)
  }, [combinados.length])

  function seleccionarResultado(resultado: ResultadoCombinado) {
    if (resultado.tipo === 'obra') {
      onElegirObra({ slug: resultado.item.slug, titulo: resultado.item.titulo })
    } else {
      onElegirTema(resultado.item)
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (combinados.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex((i) => Math.min(i + 1, combinados.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      const resultado = combinados[activeIndex]
      if (resultado) seleccionarResultado(resultado)
    }
  }

  const sinResultados = query.trim().length >= 2 && !buscando && combinados.length === 0

  return (
    <div className={styles.wrapper}>
      <h1 className={styles.title}>¿Sobre qué obra o tema quieres publicar?</h1>

      <input
        className={styles.searchInput}
        type="text"
        placeholder="Buscar obra o tema..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        autoFocus
      />

      {combinados.length > 0 && (
        <div className={styles.results}>
          {combinados.map((resultado, i) => {
            const activa = i === activeIndex
            if (resultado.tipo === 'obra') {
              const obra = resultado.item
              return (
                <button
                  key={`obra-${obra.id}`}
                  type="button"
                  className={`${styles.resultRow} ${activa ? styles.resultRowActive : ''}`}
                  onClick={() => seleccionarResultado(resultado)}
                >
                  <img className={styles.resultThumb} src={obra.imagen_url} alt="" />
                  <span className={styles.resultTitulo}>{obra.titulo}</span>
                </button>
              )
            }
            const tema = resultado.item
            return (
              <button
                key={`tema-${tema.id}`}
                type="button"
                className={`${styles.resultRow} ${activa ? styles.resultRowActive : ''}`}
                onClick={() => seleccionarResultado(resultado)}
              >
                <span className={styles.resultTag} aria-hidden="true">#</span>
                <span>
                  <span className={styles.resultTitulo}>{tema.nombre}</span>
                  <span className={styles.resultSubtitulo}>{tema.obra_titulo}</span>
                </span>
              </button>
            )
          })}
        </div>
      )}

      {sinResultados && <p className={styles.hint}>Sin resultados para "{query}".</p>}
    </div>
  )
}