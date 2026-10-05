import styles from './PostCard.module.css'
import PostActions from './PostActions'
import SaveButton from './SaveButton'
import NarrativeLabel from '../NarrativeLabel/NarrativeLabel'
import EmocionBadge from '../Emociones/EmocionBadge'
import { emocionHaloStyle } from '../../utils/emocionHalo'
import type { FeedPost } from '../../api/feed'

interface Props {
  post: FeedPost
}

export default function PostCard({ post }: Props) {
  return (
    <article className={styles.post} style={emocionHaloStyle(post.emocion_autor)}>
      {!post.is_own_post && <SaveButton postId={post.id} guardadoInicial={post.is_saved} />}

      <div className={styles.meta}>
        <a className={styles.author} href={`/perfil/${encodeURIComponent(post.autor)}/`}>
          @{post.autor}
        </a>
        <EmocionBadge emocionAutor={post.emocion_autor} />
        <span>·</span>
        <span className={styles.narrative}>
          <span>{post.obra_titulo}</span>
          {post.referencia_narrativa && (
            <>
              <span className={styles.narrativeSeparator}>|</span>
              <NarrativeLabel unidad={post.referencia_narrativa} />
            </>
          )}
        </span>
      </div>

      <a className={styles.textLink} href={`/posts/${post.id}/`}>
        <p className={styles.text}>{post.text}</p>
        {post.imagen && <img className={styles.image} src={post.imagen} alt="" />}
      </a>

      <PostActions postId={post.id} reaccionInicial={post.user_reaction} />

      <a className={styles.commentsLink} href={`/posts/${post.id}/`}>
        {post.comments_count} comentarios
      </a>
    </article>
  )
}