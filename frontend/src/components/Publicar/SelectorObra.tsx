import { useEffect, useMemo, useState, type KeyboardEvent } from 'react'
import styles from './SelectorObra.module.css'
import SugerirObraEnlace from '../SugerirObra/SugerirObraEnlace'
import SugerirObraModal from '../SugerirObra/SugerirObraModal'
import { fetchObrasPublicar, type ObraPublicable, type TemaPublicable } from '../../api/publicar'

export interface ObraSeleccionada {
  slug: string
  titulo: string
}

interface Props {
  seleccion: ObraSeleccionada | null
  onElegirObra: (obra: ObraSeleccionada) => void
  onElegirTema: (tema: TemaPublicable) => void
  onCambiar: () => void
}

type ResultadoCombinado =
  | { tipo: 'obra'; item: ObraPublicable }
  | { tipo: 'tema'; item: TemaPublicable }

const MAX_TEMAS = 8

function normalizar(texto: string) {
  return texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
}

// Primer campo del formulario de publicar: solo obras/temas de la biblioteca del usuario.
export default function SelectorObra({ seleccion, onElegirObra, onElegirTema, onCambiar }: Props) {
  const [obras, setObras] = useState<ObraPublicable[] | null>(null)
  const [temas, setTemas] = useState<TemaPublicable[]>([])
  const [errorCarga, setErrorCarga] = useState(false)
  const [query, setQuery] = useState('')
  const [abierto, setAbierto] = useState(false)
  const [activeIndex, setActiveIndex] = useState(0)
  // Título con el que se abre el modal de sugerir obra; null = cerrado.
  const [sugerirObra, setSugerirObra] = useState<string | null>(null)

  useEffect(() => {
    fetchObrasPublicar()
      .then((datos) => {
        setObras(datos.obras)
        setTemas(datos.temas)
      })
      .catch(() => setErrorCarga(true))
  }, [])

  const combinados: ResultadoCombinado[] = useMemo(() => {
    if (!obras) return []
    const q = normalizar(query.trim())
    const obrasFiltradas = q ? obras.filter((o) => normalizar(o.titulo).includes(q)) : obras
    // Sin texto solo se listan obras: los temas pueden ser muchos.
    const temasFiltrados = q ? temas.filter((t) => normalizar(t.nombre).includes(q)).slice(0, MAX_TEMAS) : []
    return [
      ...obrasFiltradas.map((item) => ({ tipo: 'obra' as const, item })),
      ...temasFiltrados.map((item) => ({ tipo: 'tema' as const, item })),
    ]
  }, [obras, temas, query])

  useEffect(() => {
    setActiveIndex(0)
  }, [query])

  function seleccionarResultado(resultado: ResultadoCombinado) {
    setQuery('')
    setAbierto(false)
    if (resultado.tipo === 'obra') {
      onElegirObra({ slug: resultado.item.slug, titulo: resultado.item.titulo })
    } else {
      onElegirTema(resultado.item)
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Escape') {
      if (query) setQuery('')
      else setAbierto(false)
      return
    }
    if (!abierto) setAbierto(true)
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

  if (seleccion) {
    return (
      <div className={styles.field}>
        <span className={styles.label}>Obra</span>
        <div className={styles.seleccion}>
          <span className={styles.seleccionTitulo}>{seleccion.titulo}</span>
          <button type="button" className={styles.cambiar} onClick={onCambiar}>
            Cambiar
          </button>
        </div>
      </div>
    )
  }

  const bibliotecaVacia = obras !== null && obras.length === 0
  const sinResultados = obras !== null && !bibliotecaVacia && query.trim() !== '' && combinados.length === 0

  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor="publicar-obra">
        ¿Sobre qué obra o tema de tu biblioteca quieres publicar?
      </label>

      <div className={styles.buscador}>
        <input
          id="publicar-obra"
          className={styles.searchInput}
          type="text"
          placeholder={obras === null && !errorCarga ? 'Cargando tu biblioteca...' : 'Filtrar tus obras o temas...'}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setAbierto(true)
          }}
          onFocus={() => setAbierto(true)}
          onBlur={() => setAbierto(false)}
          onKeyDown={handleKeyDown}
          disabled={bibliotecaVacia || errorCarga}
          autoComplete="off"
          autoFocus
        />

        {abierto && combinados.length > 0 && (
          <div className={styles.results}>
            {combinados.map((resultado, i) => {
              const activa = i === activeIndex
              const clase = `${styles.resultRow} ${activa ? styles.resultRowActive : ''}`
              // preventDefault en mousedown: el input no pierde el foco antes del click.
              if (resultado.tipo === 'obra') {
                const obra = resultado.item
                return (
                  <button
                    key={`obra-${obra.id}`}
                    type="button"
                    className={clase}
                    onMouseDown={(e) => e.preventDefault()}
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
                  className={clase}
                  onMouseDown={(e) => e.preventDefault()}
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
      </div>

      {bibliotecaVacia && (
        <p className={styles.hint}>
          Aún no sigues ninguna obra. Síguela desde Descubrir o declara tu progreso para poder publicar.
        </p>
      )}
      {errorCarga && <p className={styles.hint}>No se pudo cargar tu biblioteca. Recarga la página.</p>}
      {sinResultados && (
        <>
          <p className={styles.hint}>
            Ninguna obra de tu biblioteca coincide con "{query}". Si ya está en el catálogo, síguela desde el
            buscador para poder publicar sobre ella.
          </p>
          <SugerirObraEnlace onClick={() => setSugerirObra(query.trim())} texto="¿No está en el catálogo? Sugiérela" />
        </>
      )}

      {sugerirObra !== null && (
        <SugerirObraModal tituloInicial={sugerirObra} onClose={() => setSugerirObra(null)} />
      )}
    </div>
  )
}