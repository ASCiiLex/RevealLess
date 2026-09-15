import styles from './PostCard.module.css'
import ReactionBar from './ReactionBar'
import NarrativeLabel from '../NarrativeLabel/NarrativeLabel'
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

        {post.referencia_narrativa && (
          <>
            <span>·</span>
            <NarrativeLabel unidad={post.referencia_narrativa} />
          </>
        )}
      </div>

      <a className={styles.textLink} href={`/posts/${post.id}/react/`}>
        <p className={styles.text}>{post.text}</p>

        {post.imagen && (
          <img className={styles.image} src={post.imagen} alt="" />
        )}
      </a>

      <ReactionBar
        postId={post.id}
        reaccionInicial={post.user_reaction}
        contadorInicial={post.likes_count}
      />

      <a className={styles.commentsLink} href={`/posts/${post.id}/react/`}>
        {post.comments_count} comentarios
      </a>
    </article>
  )
}