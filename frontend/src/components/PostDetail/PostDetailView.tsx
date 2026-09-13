import { useEffect, useState } from 'react'
import styles from './PostDetailView.module.css'
import CommentItem from './CommentItem'
import ReactionBar from '../Feed/ReactionBar'
import { fetchPostDetail, addComment, type PostDetail } from '../../api/postDetail'

interface Props {
  postId: number
}

export default function PostDetailView({ postId }: Props) {
  const [detalle, setDetalle] = useState<PostDetail | null>(null)
  const [nuevoComentario, setNuevoComentario] = useState('')

  useEffect(() => {
    fetchPostDetail(postId).then(setDetalle)
  }, [postId])

  async function handleComentar() {
    if (!nuevoComentario.trim() || !detalle) return
    const nuevo = await addComment(postId, nuevoComentario)
    setDetalle({
      ...detalle,
      comments: [
        {
          id: nuevo.id,
          user: nuevo.user,
          avatar: '/static/img/default_profile.jpg',
          text: nuevo.text,
          created_at: nuevo.created_at,
          parent_id: null,
          reactions_count: 0,
          user_reaction: null,
          replies: [],
        },
        ...detalle.comments,
      ],
    })
    setNuevoComentario('')
  }

  if (!detalle) {
    return null
  }

  const { post } = detalle

  return (
    <div className={styles.wrapper}>
      <div className={styles.postCard}>
        <div className={styles.meta}>
          <img className={styles.avatar} src={post.autor_avatar} alt="" />
          <div>
            <div className={styles.author}>@{post.autor}</div>
            <div className={styles.obra}>{post.obra_titulo}</div>
          </div>
        </div>

        <p className={styles.text}>{post.text}</p>
        {post.imagen && <img className={styles.image} src={post.imagen} alt="" />}

        <ReactionBar
          postId={post.id}
          reaccionInicial={detalle.post_reaction}
          contadorInicial={post.likes_count}
        />
      </div>

      <h2 className={styles.commentsTitle}>Comentarios ({detalle.comments.length})</h2>

      <div className={styles.commentForm}>
        <input
          className={styles.commentInput}
          type="text"
          value={nuevoComentario}
          onChange={(e) => setNuevoComentario(e.target.value)}
          placeholder="Escribe un comentario..."
          onKeyDown={(e) => e.key === 'Enter' && handleComentar()}
        />
        <button className={styles.commentSubmit} onClick={handleComentar}>
          Enviar
        </button>
      </div>

      {detalle.comments.length === 0 ? (
        <p className={styles.empty}>No hay comentarios todavía.</p>
      ) : (
        detalle.comments.map((c) => <CommentItem key={c.id} comment={c} postId={postId} />)
      )}
    </div>
  )
}