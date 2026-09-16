import { useEffect, useState } from 'react'
import styles from './PostDetailView.module.css'
import CommentItem from './CommentItem'
import ReactionBar from '../Feed/ReactionBar'
import NarrativeLabel from '../NarrativeLabel/NarrativeLabel'
import EmocionBadge from '../Emociones/EmocionBadge'
import EmocionSelector from '../Emociones/EmocionSelector'
import EditPostForm from './EditPostForm'
import { emocionHaloStyle } from '../../utils/emocionHalo'
import { fetchPostDetail, addComment, type PostDetail } from '../../api/postDetail'
import type { FeedPost } from '../../api/feed'

interface Props {
  postId: number
}

export default function PostDetailView({ postId }: Props) {
  const [detalle, setDetalle] = useState<PostDetail | null>(null)
  const [nuevoComentario, setNuevoComentario] = useState('')
  const [emocionComentario, setEmocionComentario] = useState<string | null>(null)
  const [editando, setEditando] = useState(false)

  useEffect(() => {
    fetchPostDetail(postId).then(setDetalle)
  }, [postId])

  async function handleComentar() {
    if (!nuevoComentario.trim() || !detalle) return

    const nuevo = await addComment(postId, nuevoComentario, undefined, emocionComentario)

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
          emocion_autor: nuevo.emocion_autor ?? null,
          reactions_count: 0,
          user_reaction: null,
          replies: [],
        },
        ...detalle.comments,
      ],
    })

    setNuevoComentario('')
    setEmocionComentario(null)
  }

  function handlePostActualizado(postActualizado: FeedPost) {
    if (!detalle) return

    setDetalle({ ...detalle, post: postActualizado })
    setEditando(false)
  }

  if (!detalle) {
    return null
  }

  const { post } = detalle

  return (
    <div className={styles.wrapper}>
      <div className={styles.postCard} style={emocionHaloStyle(post.emocion_autor)}>
        <div className={styles.meta}>
          <img className={styles.avatar} src={post.autor_avatar} alt="" />

          <div className={styles.authorRow}>
            <div>
              <div className={styles.author}>
                @{post.autor} <EmocionBadge emocionAutor={post.emocion_autor} />
              </div>

              <div className={styles.obra}>
                <span>{post.obra_titulo}</span>

                {post.referencia_narrativa && (
                  <>
                    <span className={styles.narrativeSeparator}>|</span>
                    <NarrativeLabel unidad={post.referencia_narrativa} />
                  </>
                )}
              </div>
            </div>

            {post.is_own_post && (
              <button className={styles.editButton} onClick={() => setEditando(true)}>
                Editar
              </button>
            )}
          </div>
        </div>

        <p className={styles.text}>{post.text}</p>

        {post.imagen && <img className={styles.image} src={post.imagen} alt="" />}

        <ReactionBar
          targetId={post.id}
          reaccionInicial={detalle.post_reaction}
        />
      </div>

      {editando && (
        <EditPostForm
          post={post}
          onGuardado={handlePostActualizado}
          onCancelar={() => setEditando(false)}
        />
      )}

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

      <EmocionSelector
        value={emocionComentario}
        onChange={setEmocionComentario}
        label="¿Qué emoción te produce? (opcional, para tu comentario)"
      />

      {detalle.comments.length === 0 ? (
        <p className={styles.empty}>No hay comentarios todavía.</p>
      ) : (
        detalle.comments.map((c) => (
          <CommentItem key={c.id} comment={c} postId={postId} />
        ))
      )}
    </div>
  )
}