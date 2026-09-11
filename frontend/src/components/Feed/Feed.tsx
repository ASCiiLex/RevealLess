import { useEffect, useState } from 'react'
import styles from './Feed.module.css'
import PostCard from './PostCard'
import { fetchFeed, type FeedPost } from '../../api/feed'
import { useCatalogView } from '../../context/CatalogViewContext'

export default function Feed() {
  const { obraFiltro } = useCatalogView()
  const [posts, setPosts] = useState<FeedPost[] | null>(null)

  useEffect(() => {
    setPosts(null)
    fetchFeed(obraFiltro)
      .then((data) => setPosts(data.results))
      .catch(() => setPosts([]))
  }, [obraFiltro])

  if (!posts) {
    return null
  }

  return (
    <div className={styles.feed}>
      {posts.length === 0 ? (
        <p className={styles.empty}>
          {obraFiltro
            ? 'No hay publicaciones visibles de esta obra por ahora.'
            : 'Aún no hay nada que mostrar aquí. Sigue una obra o publica algo para empezar.'}
        </p>
      ) : (
        posts.map((post) => <PostCard key={post.id} post={post} />)
      )}
    </div>
  )
}