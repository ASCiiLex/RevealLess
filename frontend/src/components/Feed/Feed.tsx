import { useCallback, useEffect, useRef, useState } from 'react'
import styles from './Feed.module.css'
import PostCard from './PostCard'
import FilterHeader from './FilterHeader'
import {
  fetchFeed,
  fetchFeedPagina,
  type FeedPost,
  type PaginaFeed,
  type VistaFeed,
} from '../../api/feed'
import { fetchTemaLanding } from '../../api/temaLanding'
import { fetchPersonajeLanding } from '../../api/personajeLanding'
import { useCatalogView } from '../../context/CatalogViewContext'

interface FiltroExterno {
  tipo: 'obra' | 'hashtag' | 'tema' | 'personaje'
  valor: string
}

interface Props {
  filtroExterno?: FiltroExterno | null
  // Cambia cuando el usuario sigue o deja de seguir algo: obliga a pedir el feed de nuevo.
  version?: number
}

const MENSAJE_VACIO = {
  silenciado: 'Lo has silenciado: no verás sus publicaciones hasta reactivarlo.',
  filtro: 'No hay publicaciones visibles con este filtro por ahora.',
  biblioteca: 'Aún no hay nada que mostrar aquí. Sigue una obra o publica algo para empezar.',
  descubrir:
    'Nada que descubrir por ahora. Aquí aparece lo que puedes leer sin spoilers y aún no te llega por Biblioteca.',
}

export default function Feed({ filtroExterno, version = 0 }: Props) {
  const { view, obraFiltro, temaFiltro, personajeFiltro, filtroSilenciado } = useCatalogView()
  const [posts, setPosts] = useState<FeedPost[] | null>(null)
  const [siguiente, setSiguiente] = useState<string | null>(null)
  const [cargandoMas, setCargandoMas] = useState(false)
  const [errorMas, setErrorMas] = useState(false)
  // Título que hay que pedir aparte (tema o personaje).
  const [tituloRemoto, setTituloRemoto] = useState<string | null>(null)
  // Cada carga inicial invalida las respuestas pendientes de la anterior.
  const peticion = useRef(0)
  const centinela = useRef<HTMLDivElement>(null)

  // Con filtro externo no hay pestañas: siempre Biblioteca.
  const vista: VistaFeed = filtroExterno ? 'biblioteca' : view

  useEffect(() => {
    const id = ++peticion.current
    const vigente = () => id === peticion.current
    setPosts(null)
    setSiguiente(null)
    setCargandoMas(false)
    setErrorMas(false)
    setTituloRemoto(null)

    const aplicar = (pagina: PaginaFeed) => {
      if (!vigente()) return
      setPosts(pagina.results)
      setSiguiente(pagina.next)
    }
    const vaciar = () => {
      if (vigente()) setPosts([])
    }
    const titulo = (nombre: string) => {
      if (vigente()) setTituloRemoto(nombre)
    }

    if (filtroExterno?.tipo === 'hashtag') {
      fetchFeed({ hashtag: filtroExterno.valor }).then(aplicar).catch(vaciar)
      return
    }

    if (filtroExterno?.tipo === 'tema') {
      const temaId = Number(filtroExterno.valor)
      fetchTemaLanding(temaId).then((data) => titulo(data.nombre)).catch(() => titulo(''))
      fetchFeed({ temaId }).then(aplicar).catch(vaciar)
      return
    }

    if (filtroExterno?.tipo === 'personaje') {
      const personajeId = Number(filtroExterno.valor)
      fetchPersonajeLanding(personajeId).then((data) => titulo(data.nombre)).catch(() => titulo(''))
      fetchFeed({ personajeId }).then(aplicar).catch(vaciar)
      return
    }

    // Lomos del carrusel (sin filtro externo): tema o personaje tienen prioridad sobre obra.
    if (!filtroExterno && temaFiltro !== null) {
      fetchFeed({ temaId: temaFiltro, vista }).then(aplicar).catch(vaciar)
      return
    }

    if (!filtroExterno && personajeFiltro !== null) {
      fetchFeed({ personajeId: personajeFiltro, vista }).then(aplicar).catch(vaciar)
      return
    }

    const obraId = filtroExterno?.tipo === 'obra' ? Number(filtroExterno.valor) : obraFiltro
    fetchFeed({ obraId, vista }).then(aplicar).catch(vaciar)
  }, [obraFiltro, temaFiltro, personajeFiltro, filtroExterno, version, vista])

  const cargarMas = useCallback(() => {
    if (!siguiente || cargandoMas) return
    const id = peticion.current
    setCargandoMas(true)
    setErrorMas(false)
    fetchFeedPagina(siguiente)
      .then((pagina) => {
        if (id !== peticion.current) return
        setPosts((actuales) => {
          const previos = actuales ?? []
          const vistos = new Set(previos.map((p) => p.id))
          return [...previos, ...pagina.results.filter((p) => !vistos.has(p.id))]
        })
        setSiguiente(pagina.next)
      })
      .catch(() => {
        if (id === peticion.current) setErrorMas(true)
      })
      .finally(() => {
        if (id === peticion.current) setCargandoMas(false)
      })
  }, [siguiente, cargandoMas])

  // Se recrea tras cada carga: si el centinela sigue a la vista, pide la siguiente página.
  useEffect(() => {
    const nodo = centinela.current
    if (!nodo || !siguiente || errorMas) return
    const observador = new IntersectionObserver(
      (entradas) => {
        if (entradas[0]?.isIntersecting) cargarMas()
      },
      { rootMargin: '600px 0px' },
    )
    observador.observe(nodo)
    return () => observador.disconnect()
  }, [siguiente, errorMas, cargarMas])

  if (!posts) {
    return null
  }

  const hayFiltro =
    Boolean(filtroExterno) || obraFiltro !== null || temaFiltro !== null || personajeFiltro !== null

  const mensajeVacio = filtroSilenciado
    ? MENSAJE_VACIO.silenciado
    : hayFiltro
      ? MENSAJE_VACIO.filtro
      : MENSAJE_VACIO[vista]

  const tituloFiltro =
    filtroExterno?.tipo === 'hashtag'
      ? `#${filtroExterno.valor}`
      : filtroExterno?.tipo === 'tema' || filtroExterno?.tipo === 'personaje'
        ? tituloRemoto ?? ''
        : filtroExterno?.tipo === 'obra'
          ? posts[0]?.obra_titulo ?? 'Obra'
          : null

  const linkHrefFiltro =
    filtroExterno?.tipo === 'obra' && posts[0]
      ? `/narrative/obra/${posts[0].obra_slug}/`
      : filtroExterno?.tipo === 'tema'
        ? `/narrative/tema/${filtroExterno.valor}/`
        : filtroExterno?.tipo === 'personaje' && tituloRemoto
          ? `/narrative/personaje/${filtroExterno.valor}/`
          : undefined

  return (
    <div className={styles.feed}>
      {filtroExterno && <FilterHeader titulo={tituloFiltro ?? ''} linkHref={linkHrefFiltro} />}

      {posts.length === 0 ? (
        <p className={styles.empty}>{mensajeVacio}</p>
      ) : (
        posts.map((post) => <PostCard key={post.id} post={post} />)
      )}

      {siguiente && !errorMas && <div ref={centinela} className={styles.centinela} aria-hidden="true" />}

      {cargandoMas && <p className={styles.estado}>Cargando…</p>}

      {errorMas && (
        <button type="button" className={styles.reintentar} onClick={cargarMas}>
          No se pudieron cargar más publicaciones. Reintentar
        </button>
      )}
    </div>
  )
}