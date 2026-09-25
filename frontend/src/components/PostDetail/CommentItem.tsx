import { useRef, useState, type KeyboardEvent } from 'react'
import styles from './CommentItem.module.css'
import EmocionBadge from '../Emociones/EmocionBadge'
import EmocionPopover from '../Emociones/EmocionPopover'
import ReactionBar from '../Feed/ReactionBar'
import LinkedText from '../Text/LinkedText'
import EditCommentForm from './EditCommentForm'
import NarrativaSelector, { type NarrativaValue } from './NarrativaSelector'
import ReferenciaCruzadaAviso from '../ReferenciaCruzada/ReferenciaCruzadaAviso'
import { useMentionHashtagAutocomplete } from '../../hooks/useMentionHashtagAutocomplete'
import AutocompleteDropdown from '../Autocomplete/AutocompleteDropdown'
import type { DeteccionCruzada } from '../../api/publicar'
import type { CommentItem as CommentItemType } from '../../api/postDetail'
import { addComment, deleteComment } from '../../api/postDetail'
import type { ObraDetalle } from '../../api/suscripciones'

interface Props {
  comment: CommentItemType
  postId: number
  obraDetalle: ObraDetalle | null
  nivel?: number
  onEliminado?: (commentId: number) => void
}

// nivel 1 = raíz, nivel 2 = respuesta, nivel 3 = respuesta-a-respuesta.
// El backend permite responder en nivel 1 y 2 (crea nivel 2 y 3), y
// rechaza responder en nivel 3 (crearía un nivel 4).
const NIVEL_MAXIMO = 3

const NARRATIVA_VACIA: NarrativaValue = {
  referenciaId: null,
  fronteraId: null,
  obraCruzadaId: null,
  fronteraCruzadaId: null,
}

export default function CommentItem({ comment, postId, obraDetalle, nivel = 1, onEliminado }: Props) {
  const [replyAbierto, setReplyAbierto] = useState(false)
  const [replyTexto, setReplyTexto] = useState('')
  const [replyNarrativa, setReplyNarrativa] = useState<NarrativaValue>(NARRATIVA_VACIA)
  const [replyEmocion, setReplyEmocion] = useState<string | null>(null)
  const [replyEmocionAbierta, setReplyEmocionAbierta] = useState(false)
  const [replies, setReplies] = useState(comment.replies)
  const [editando, setEditando] = useState(false)
  const [textoActual, setTextoActual] = useState(comment.text)
  const [emocionActual, setEmocionActual] = useState(comment.emocion_autor)
  const [detecciones, setDetecciones] = useState<DeteccionCruzada[] | null>(null)
  const [eliminando, setEliminando] = useState(false)
  const [eliminado, setEliminado] = useState(false)

  const replyInputRef = useRef<HTMLInputElement>(null)
  const autocomplete = useMentionHashtagAutocomplete({
    value: replyTexto,
    onChange: setReplyTexto,
    fieldRef: replyInputRef,
  })

  async function enviarReply(overrides: {
    obraCruzadaId?: number | null
    fronteraCruzadaId?: number | null
    descartarReferenciaCruzada?: boolean
  } = {}) {
    if (!replyTexto.trim()) return

    const resultado = await addComment(postId, replyTexto, {
      parentId: comment.id,
      referenciaNarrativaId: replyNarrativa.referenciaId,
      fronteraSpoilerId: replyNarrativa.fronteraId,
      obraCruzadaId: replyNarrativa.obraCruzadaId,
      fronteraCruzadaId: replyNarrativa.fronteraCruzadaId,
      emocionAutor: replyEmocion,
      ...overrides,
    })

    if ('referenciaCruzadaDetectada' in resultado) {
      setDetecciones(resultado.detecciones)
      return
    }

    setDetecciones(null)
    setReplies((prev) => [
      ...prev,
      {
        id: resultado.id,
        user: resultado.user,
        avatar: '/static/img/default_profile.jpg',
        text: resultado.text,
        created_at: resultado.created_at,
        parent_id: comment.id,
        emocion_autor: resultado.emocion_autor,
        referencia_narrativa_id: resultado.referencia_narrativa_id,
        frontera_spoiler_id: resultado.frontera_spoiler_id,
        frontera_origen: resultado.frontera_origen,
        obra_cruzada_id: resultado.obra_cruzada_id,
        frontera_cruzada_id: resultado.frontera_cruzada_id,
        is_own_comment: true,
        reactions_count: 0,
        user_reaction: null,
        replies: [],
      },
    ])
    setReplyTexto('')
    setReplyNarrativa(NARRATIVA_VACIA)
    setReplyEmocion(null)
    setReplyAbierto(false)
  }

  function handleGuardadoEdicion(datos: { text: string; emocion_autor: string | null }) {
    setTextoActual(datos.text)
    setEmocionActual(datos.emocion_autor)
    setEditando(false)
  }

  function handleKeyDownReply(e: KeyboardEvent<HTMLInputElement>) {
    if (autocomplete.handleKeyDown(e)) return
    if (e.key === 'Enter') enviarReply()
  }

  function handleReplyEliminado(replyId: number) {
    setReplies((prev) => prev.filter((r) => r.id !== replyId))
  }

  async function handleEliminar() {
    if (eliminando) return
    if (!window.confirm('¿Eliminar este comentario? Esta acción no se puede deshacer.')) return

    setEliminando(true)
    try {
      await deleteComment(comment.id)
      setEliminado(true)
      onEliminado?.(comment.id)
    } catch {
      // Sin cambios visibles: el comentario sigue mostrándose si falla el borrado.
    } finally {
      setEliminando(false)
    }
  }

  if (eliminado) {
    return null
  }

  const puedeResponder = nivel < NIVEL_MAXIMO

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
            <div className={styles.inputWrap}>
              <input
                ref={replyInputRef}
                className={styles.replyInput}
                type="text"
                value={replyTexto}
                onChange={(e) => autocomplete.handleChange(e.target.value)}
                onFocus={() => setReplyEmocionAbierta(true)}
                onBlur={() => {
                  setTimeout(() => setReplyEmocionAbierta(false), 150)
                  setTimeout(autocomplete.cerrar, 150)
                }}
                placeholder="Escribe una respuesta..."
                onKeyDown={handleKeyDownReply}
              />
              {autocomplete.suggestions.length > 0 ? (
                <AutocompleteDropdown
                  suggestions={autocomplete.suggestions}
                  activeIndex={autocomplete.activeIndex}
                  onSelect={autocomplete.seleccionar}
                />
              ) : (
                <EmocionPopover
                  visible={replyEmocionAbierta}
                  value={replyEmocion}
                  onSelect={setReplyEmocion}
                />
              )}
            </div>
            <button className={styles.quitar} onClick={() => enviarReply()}>Enviar</button>
          </div>
          {obraDetalle && (
            <NarrativaSelector
              obraLocal={obraDetalle}
              value={replyNarrativa}
              onChange={setReplyNarrativa}
            />
          )}
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
              onEliminado={handleReplyEliminado}
            />
          ))}
        </div>
      )}

      {detecciones && (
        <ReferenciaCruzadaAviso
          detecciones={detecciones}
          onConfirmar={(obraCruzadaId, fronteraCruzadaId) => {
            enviarReply({ obraCruzadaId, fronteraCruzadaId })
          }}
          onDescartar={() => {
            enviarReply({ descartarReferenciaCruzada: true })
          }}
          onCancelar={() => setDetecciones(null)}
        />
      )}
    </div>
  )
}