import { useEffect, useState } from 'react'
import styles from './Feed.module.css'
import PostCard from './PostCard'
import FilterHeader from './FilterHeader'
import { fetchFeed, type FeedPost } from '../../api/feed'
import { useCatalogView } from '../../context/CatalogViewContext'

interface FiltroExterno {
  tipo: 'obra' | 'hashtag'
  valor: string
}

interface Props {
  filtroExterno?: FiltroExterno | null
}

export default function Feed({ filtroExterno }: Props) {
  const { obraFiltro } = useCatalogView()
  const [posts, setPosts] = useState<FeedPost[] | null>(null)

  useEffect(() => {
    setPosts(null)

    if (filtroExterno?.tipo === 'hashtag') {
      fetchFeed(undefined, filtroExterno.valor)
        .then((data) => setPosts(data.results))
        .catch(() => setPosts([]))
      return
    }

    const obraId = filtroExterno?.tipo === 'obra' ? Number(filtroExterno.valor) : obraFiltro
    fetchFeed(obraId)
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
      : filtroExterno?.tipo === 'obra'
        ? posts[0]?.obra_titulo ?? 'Obra'
        : null

  return (
    <div className={styles.feed}>
      {filtroExterno && <FilterHeader titulo={tituloFiltro ?? ''} />}

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