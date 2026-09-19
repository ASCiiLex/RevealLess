import { useEffect, useState } from 'react'
import styles from './PostDetailView.module.css'
import CommentItem from './CommentItem'
import ReactionBar from '../Feed/ReactionBar'
import NarrativeLabel from '../NarrativeLabel/NarrativeLabel'
import EmocionBadge from '../Emociones/EmocionBadge'
import EmocionPopover from '../Emociones/EmocionPopover'
import NarrativaSelector, { type NarrativaValue } from './NarrativaSelector'
import EditPostForm from './EditPostForm'
import { emocionHaloStyle } from '../../utils/emocionHalo'
import { fetchPostDetail, addComment, type PostDetail } from '../../api/postDetail'
import { fetchObraDetalle, type ObraDetalle } from '../../api/suscripciones'
import type { FeedPost } from '../../api/feed'

interface Props {
  postId: number
}

const NARRATIVA_VACIA: NarrativaValue = {
  referenciaId: null,
  fronteraId: null,
  obraCruzadaId: null,
  fronteraCruzadaId: null,
}

export default function PostDetailView({ postId }: Props) {
  const [detalle, setDetalle] = useState<PostDetail | null>(null)
  const [obraDetalle, setObraDetalle] = useState<ObraDetalle | null>(null)
  const [nuevoComentario, setNuevoComentario] = useState('')
  const [emocionComentario, setEmocionComentario] = useState<string | null>(null)
  const [emocionAbierta, setEmocionAbierta] = useState(false)
  const [narrativa, setNarrativa] = useState<NarrativaValue>(NARRATIVA_VACIA)
  const [editando, setEditando] = useState(false)

  useEffect(() => {
    fetchPostDetail(postId).then(setDetalle)
  }, [postId])

  useEffect(() => {
    if (detalle) {
      fetchObraDetalle(detalle.post.obra_slug).then(setObraDetalle)
    }
  }, [detalle?.post.obra_slug])

  async function handleComentar() {
    if (!nuevoComentario.trim() || !detalle) return

    const nuevo = await addComment(postId, nuevoComentario, {
      emocionAutor: emocionComentario,
      referenciaNarrativaId: narrativa.referenciaId,
      fronteraSpoilerId: narrativa.fronteraId,
      obraCruzadaId: narrativa.obraCruzadaId,
      fronteraCruzadaId: narrativa.fronteraCruzadaId,
    })

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
          referencia_narrativa_id: nuevo.referencia_narrativa_id ?? null,
          frontera_spoiler_id: nuevo.frontera_spoiler_id ?? null,
          frontera_origen: nuevo.frontera_origen ?? 'heredado_post',
          obra_cruzada_id: nuevo.obra_cruzada_id ?? null,
          frontera_cruzada_id: nuevo.frontera_cruzada_id ?? null,
          is_own_comment: true,
          reactions_count: 0,
          user_reaction: null,
          replies: [],
        },
        ...detalle.comments,
      ],
    })

    setNuevoComentario('')
    setEmocionComentario(null)
    setNarrativa(NARRATIVA_VACIA)
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
        <div className={styles.commentInputRow}>
          <div className={styles.inputWrap}>
            <input
              className={styles.commentInput}
              type="text"
              value={nuevoComentario}
              onChange={(e) => setNuevoComentario(e.target.value)}
              onFocus={() => setEmocionAbierta(true)}
              onBlur={() => setTimeout(() => setEmocionAbierta(false), 150)}
              placeholder="Escribe un comentario..."
              onKeyDown={(e) => e.key === 'Enter' && handleComentar()}
            />
            <EmocionPopover
              visible={emocionAbierta}
              value={emocionComentario}
              onSelect={setEmocionComentario}
            />
          </div>

          <button className={styles.commentSubmit} onClick={handleComentar}>
            Enviar
          </button>
        </div>

        {obraDetalle && (
          <NarrativaSelector
            obraLocal={obraDetalle}
            value={narrativa}
            onChange={setNarrativa}
          />
        )}
      </div>

      {detalle.comments.length === 0 ? (
        <p className={styles.empty}>No hay comentarios todavía.</p>
      ) : (
        detalle.comments.map((c) => (
          <CommentItem
            key={c.id}
            comment={c}
            postId={postId}
            obraDetalle={obraDetalle}
          />
        ))
      )}
    </div>
  )
}