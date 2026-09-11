import styles from './PostCard.module.css'
import type { FeedPost } from '../../api/feed'

interface Props {
  post: FeedPost
}

export default function PostCard({ post }: Props) {
  return (
    <article className={styles.post}>
      <div className={styles.meta}>
        <span className={styles.author}>@{post.autor}</span>
        <span>·</span>
        <span>{post.obra_titulo}</span>
      </div>

      <p className={styles.text}>{post.text}</p>

      {post.imagen && <img className={styles.image} src={post.imagen} alt="" />}

      <div className={styles.stats}>
        {post.likes_count} reacciones · {post.comments_count} comentarios
      </div>
    </article>
  )
}