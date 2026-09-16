import { useState } from 'react'
import styles from './CommentItem.module.css'
import EmocionBadge from '../Emociones/EmocionBadge'
import ReactionBar from '../Feed/ReactionBar'
import type { CommentItem as CommentItemType } from '../../api/postDetail'
import { addComment } from '../../api/postDetail'

interface Props {
  comment: CommentItemType
  postId: number
  nivel?: number
}

const NIVEL_MAXIMO = 3

export default function CommentItem({ comment, postId, nivel = 1 }: Props) {
  const [replyAbierto, setReplyAbierto] = useState(false)
  const [replyTexto, setReplyTexto] = useState('')
  const [replies, setReplies] = useState(comment.replies)

  async function handleReply() {
    if (!replyTexto.trim()) return
    const nuevo = await addComment(postId, replyTexto, comment.id)
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
        reactions_count: 0,
        user_reaction: null,
        replies: [],
      },
    ])
    setReplyTexto('')
    setReplyAbierto(false)
  }

  const puedeResponder = nivel < NIVEL_MAXIMO

  return (
    <div className={styles.comment}>
      <div className={styles.header}>
        <img className={styles.avatar} src={comment.avatar} alt="" />
        <span className={styles.username}>@{comment.user}</span>
        <EmocionBadge emocionAutor={comment.emocion_autor} />
      </div>
      <p className={styles.text}>{comment.text}</p>

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
      )}

      {replies.length > 0 && (
        <div className={styles.replies}>
          {replies.map((reply) => (
            <CommentItem key={reply.id} comment={reply} postId={postId} nivel={nivel + 1} />
          ))}
        </div>
      )}
    </div>
  )
}