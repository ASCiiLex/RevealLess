import { useEffect, useState } from 'react'
import styles from './Feed.module.css'
import PostCard from './PostCard'
import FilterHeader from './FilterHeader'
import { fetchFeed, type FeedPost } from '../../api/feed'
import { fetchTemaLanding } from '../../api/temaLanding'
import { fetchFeedPersonaje, fetchPersonajeLanding } from '../../api/personajeLanding'
import { useCatalogView } from '../../context/CatalogViewContext'

interface FiltroExterno {
  tipo: 'obra' | 'hashtag' | 'tema' | 'personaje'
  valor: string
}

interface Props {
  filtroExterno?: FiltroExterno | null
}

export default function Feed({ filtroExterno }: Props) {
  const { obraFiltro } = useCatalogView()
  const [posts, setPosts] = useState<FeedPost[] | null>(null)
  // Título que hay que pedir aparte (tema o personaje).
  const [tituloRemoto, setTituloRemoto] = useState<string | null>(null)

  useEffect(() => {
    setPosts(null)
    setTituloRemoto(null)

    if (filtroExterno?.tipo === 'hashtag') {
      fetchFeed({ hashtag: filtroExterno.valor })
        .then((data) => setPosts(data.results))
        .catch(() => setPosts([]))
      return
    }

    if (filtroExterno?.tipo === 'tema') {
      const temaId = Number(filtroExterno.valor)
      fetchTemaLanding(temaId).then((data) => setTituloRemoto(data.nombre))
      fetchFeed({ temaId })
        .then((data) => setPosts(data.results))
        .catch(() => setPosts([]))
      return
    }

    if (filtroExterno?.tipo === 'personaje') {
      const personajeId = Number(filtroExterno.valor)
      fetchPersonajeLanding(personajeId)
        .then((data) => setTituloRemoto(data.nombre))
        .catch(() => setTituloRemoto(''))
      fetchFeedPersonaje(personajeId)
        .then(setPosts)
        .catch(() => setPosts([]))
      return
    }

    const obraId = filtroExterno?.tipo === 'obra' ? Number(filtroExterno.valor) : obraFiltro
    fetchFeed({ obraId })
      .then((data) => setPosts(data.results))
      .catch(() => setPosts([]))
  }, [obraFiltro, filtroExterno])

  if (!posts) {
    return null
  }

  const hayFiltro = Boolean(filtroExterno) || obraFiltro !== null

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
        <p className={styles.empty}>
          {hayFiltro
            ? 'No hay publicaciones visibles con este filtro por ahora.'
            : 'Aún no hay nada que mostrar aquí. Sigue una obra o publica algo para empezar.'}
        </p>
      ) : (
        posts.map((post) => <PostCard key={post.id} post={post} />)
      )}
    </div>
  )
}