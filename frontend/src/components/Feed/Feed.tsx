import { useEffect, useState } from 'react'
import styles from './Feed.module.css'
import PostCard from './PostCard'
import { fetchFeed, type FeedPost } from '../../api/feed'

export default function Feed() {
  const [posts, setPosts] = useState<FeedPost[] | null>(null)

  useEffect(() => {
    fetchFeed()
      .then((data) => setPosts(data.results))
      .catch(() => setPosts([]))
  }, [])

  if (!posts) {
    return null
  }

  return (
    <div className={styles.feed}>
      {posts.length === 0 ? (
        <p className={styles.empty}>
          Aún no hay nada que mostrar aquí. Sigue una obra o publica algo para empezar.
        </p>
      ) : (
        posts.map((post) => <PostCard key={post.id} post={post} />)
      )}
    </div>
  )
}