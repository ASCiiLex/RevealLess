import { useState } from 'react'
import styles from './CommentItem.module.css'
import ComentarioForm from './ComentarioForm'
import EditCommentForm from './EditCommentForm'
import EmocionBadge from '../Emociones/EmocionBadge'
import ReactionBar from '../Feed/ReactionBar'
import LinkedText from '../Text/LinkedText'
import { deleteComment, type CommentItem as CommentItemType } from '../../api/comentarios'
import type { ObraDetalle } from '../../api/suscripciones'

interface Props {
  comment: CommentItemType
  postId: number
  obraDetalle: ObraDetalle | null
  nivel?: number
  onEliminado: (commentId: number) => void
}

// 1 = raíz, 2 = respuesta, 3 = respuesta-a-respuesta; el backend rechaza un 4º nivel.
const NIVEL_MAXIMO = 3

export default function CommentItem({ comment, postId, obraDetalle, nivel = 1, onEliminado }: Props) {
  const [replyAbierto, setReplyAbierto] = useState(false)
  const [replies, setReplies] = useState(comment.replies)
  const [editando, setEditando] = useState(false)
  const [textoActual, setTextoActual] = useState(comment.text)
  const [emocionActual, setEmocionActual] = useState(comment.emocion_autor)
  const [eliminando, setEliminando] = useState(false)

  function handleReplyCreada(reply: CommentItemType) {
    setReplies((prev) => [...prev, reply])
    setReplyAbierto(false)
  }

  function handleReplyEliminada(replyId: number) {
    setReplies((prev) => prev.filter((r) => r.id !== replyId))
  }

  function handleGuardadoEdicion(datos: { text: string; emocion_autor: string | null }) {
    setTextoActual(datos.text)
    setEmocionActual(datos.emocion_autor)
    setEditando(false)
  }

  async function handleEliminar() {
    if (eliminando) return
    if (!window.confirm('¿Eliminar este comentario? Esta acción no se puede deshacer.')) return

    setEliminando(true)
    try {
      await deleteComment(comment.id)
      onEliminado(comment.id)
    } catch {
      // Si falla, el comentario sigue visible.
      setEliminando(false)
    }
  }

  return (
    <div className={styles.comment}>
      <div className={styles.header}>
        <img className={styles.avatar} src={comment.avatar} alt="" />
        <span className={styles.username}>@{comment.user}</span>
        <EmocionBadge emocionAutor={emocionActual} />
        {comment.is_own_comment && (
          <>
            <button className={styles.editButton} onClick={() => setEditando(true)}>
              Editar
            </button>
            <button className={styles.editButton} onClick={handleEliminar} disabled={eliminando}>
              {eliminando ? 'Eliminando...' : 'Eliminar'}
            </button>
          </>
        )}
      </div>

      <p className={styles.text}><LinkedText text={textoActual} /></p>

      <div className={styles.actions}>
        <ReactionBar targetId={comment.id} target="comment" reaccionInicial={comment.user_reaction} />
        {nivel < NIVEL_MAXIMO && (
          <button className={styles.replyButton} onClick={() => setReplyAbierto((v) => !v)}>
            Responder
          </button>
        )}
      </div>

      {replyAbierto && (
        <ComentarioForm
          postId={postId}
          parentId={comment.id}
          obraDetalle={obraDetalle}
          variante="respuesta"
          onCreado={handleReplyCreada}
        />
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
              onEliminado={handleReplyEliminada}
            />
          ))}
        </div>
      )}
    </div>
  )
}