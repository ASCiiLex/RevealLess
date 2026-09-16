import { useState } from 'react'
import styles from './CommentItem.module.css'
import EmocionBadge from '../Emociones/EmocionBadge'
import EmocionSelector from '../Emociones/EmocionSelector'
import ReactionBar from '../Feed/ReactionBar'
import EditCommentForm from './EditCommentForm'
import NarrativaSelector from './NarrativaSelector'
import type { CommentItem as CommentItemType } from '../../api/postDetail'
import { addComment } from '../../api/postDetail'
import type { ObraDetalle } from '../../api/suscripciones'

interface Props {
  comment: CommentItemType
  postId: number
  obraDetalle: ObraDetalle | null
  nivel?: number
}

const NIVEL_MAXIMO = 3

export default function CommentItem({ comment, postId, obraDetalle, nivel = 1 }: Props) {
  const [replyAbierto, setReplyAbierto] = useState(false)
  const [replyTexto, setReplyTexto] = useState('')
  const [replyReferencia, setReplyReferencia] = useState<number | null>(null)
  const [replyFrontera, setReplyFrontera] = useState<number | null>(null)
  const [replyEmocion, setReplyEmocion] = useState<string | null>(null)
  const [replies, setReplies] = useState(comment.replies)
  const [editando, setEditando] = useState(false)
  const [textoActual, setTextoActual] = useState(comment.text)
  const [emocionActual, setEmocionActual] = useState(comment.emocion_autor)

  async function handleReply() {
    if (!replyTexto.trim()) return
    const nuevo = await addComment(postId, replyTexto, {
      parentId: comment.id,
      referenciaNarrativaId: replyReferencia,
      fronteraSpoilerId: replyFrontera,
      emocionAutor: replyEmocion,
    })
    setReplies((prev) => [
      ...prev,
      {
        id: nuevo.id,
        user: nuevo.user,
        avatar: '/static/img/default_profile.jpg',
        text: nuevo.text,
        created_at: nuevo.created_at,
        parent_id: comment.id,
        emocion_autor: nuevo.emocion_autor ?? null,
        referencia_narrativa_id: nuevo.referencia_narrativa_id ?? null,
        frontera_spoiler_id: nuevo.frontera_spoiler_id ?? null,
        frontera_origen: nuevo.frontera_origen ?? 'heredado_post',
        is_own_comment: true,
        reactions_count: 0,
        user_reaction: null,
        replies: [],
      },
    ])
    setReplyTexto('')
    setReplyReferencia(null)
    setReplyFrontera(null)
    setReplyEmocion(null)
    setReplyAbierto(false)
  }

  function handleGuardadoEdicion(datos: { text: string; emocion_autor: string | null }) {
    setTextoActual(datos.text)
    setEmocionActual(datos.emocion_autor)
    setEditando(false)
  }

  const puedeResponder = nivel < NIVEL_MAXIMO

  return (
    <div className={styles.comment}>
      <div className={styles.header}>
        <img className={styles.avatar} src={comment.avatar} alt="" />
        <span className={styles.username}>@{comment.user}</span>
        <EmocionBadge emocionAutor={emocionActual} />
        {comment.is_own_comment && (
          <button className={styles.editButton} onClick={() => setEditando(true)}>
            Editar
          </button>
        )}
      </div>
      <p className={styles.text}>{textoActual}</p>

      <div className={styles.actions}>
        <ReactionBar
          targetId={comment.id}
          target="comment"
          reaccionInicial={comment.user_reaction}
        />
        {puedeResponder && (
          <button className={styles.replyButton} onClick={() => setReplyAbierto((v) => !v)}>
            Responder
          </button>
        )}
      </div>

      {replyAbierto && (
        <div className={styles.replyForm}>
          <div className={styles.replyInputRow}>
            <input
              className={styles.replyInput}
              type="text"
              value={replyTexto}
              onChange={(e) => setReplyTexto(e.target.value)}
              placeholder="Escribe una respuesta..."
              onKeyDown={(e) => e.key === 'Enter' && handleReply()}
            />
            <button className={styles.quitar} onClick={handleReply}>Enviar</button>
          </div>
          {obraDetalle && (
            <NarrativaSelector
              detalle={obraDetalle}
              referenciaId={replyReferencia}
              fronteraId={replyFrontera}
              onChangeReferencia={setReplyReferencia}
              onChangeFrontera={setReplyFrontera}
            />
          )}
          <EmocionSelector
            value={replyEmocion}
            onChange={setReplyEmocion}
            label="¿Quieres añadir emoción de contexto? (opcional)"
          />
        </div>
      )}

      {editando && (
        <EditCommentForm
          comment={comment}
          obraDetalle={obraDetalle}
          onGuardado={handleGuardadoEdicion}
          onCancelar={() => setEditando(false)}
        />
      )}

      {replies.length > 0 && (
        <div className={styles.replies}>
          {replies.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              postId={postId}
              obraDetalle={obraDetalle}
              nivel={nivel + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}