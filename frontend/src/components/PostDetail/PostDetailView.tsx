import { useEffect, useRef, useState } from 'react'
import styles from './PostDetailView.module.css'
import CommentItem from './CommentItem'
import PostActions from '../Feed/PostActions'
import SaveButton from '../Feed/SaveButton'
import LinkedText from '../Text/LinkedText'
import NarrativeLabel from '../NarrativeLabel/NarrativeLabel'
import EmocionBadge from '../Emociones/EmocionBadge'
import EmocionPopover from '../Emociones/EmocionPopover'
import { useMentionHashtagAutocomplete } from '../../hooks/useMentionHashtagAutocomplete'
import AutocompleteDropdown from '../Autocomplete/AutocompleteDropdown'
import NarrativaSelector, { type NarrativaValue } from './NarrativaSelector'
import EditPostForm from './EditPostForm'
import ReferenciaCruzadaAviso from '../ReferenciaCruzada/ReferenciaCruzadaAviso'
import type { DeteccionCruzada } from '../../api/publicar'
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
  const [detecciones, setDetecciones] = useState<DeteccionCruzada[] | null>(null)

  const comentarioInputRef = useRef<HTMLInputElement>(null)
  const autocomplete = useMentionHashtagAutocomplete({
    value: nuevoComentario,
    onChange: setNuevoComentario,
    fieldRef: comentarioInputRef,
  })

  useEffect(() => {
    fetchPostDetail(postId).then(setDetalle)
  }, [postId])

  useEffect(() => {
    if (detalle) {
      fetchObraDetalle(detalle.post.obra_slug).then(setObraDetalle)
    }
  }, [detalle?.post.obra_slug])

  function agregarComentarioAlEstado(nuevo: {
    id: number
    user: string
    text: string
    created_at: string
    emocion_autor: string | null
    referencia_narrativa_id: number | null
    frontera_spoiler_id: number | null
    frontera_origen: string
    obra_cruzada_id: number | null
    frontera_cruzada_id: number | null
  }) {
    if (!detalle) return
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
          emocion_autor: nuevo.emocion_autor,
          referencia_narrativa_id: nuevo.referencia_narrativa_id,
          frontera_spoiler_id: nuevo.frontera_spoiler_id,
          frontera_origen: nuevo.frontera_origen,
          obra_cruzada_id: nuevo.obra_cruzada_id,
          frontera_cruzada_id: nuevo.frontera_cruzada_id,
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

  async function enviarComentario(overrides: {
    obraCruzadaId?: number | null
    fronteraCruzadaId?: number | null
    descartarReferenciaCruzada?: boolean
  } = {}) {
    if (!nuevoComentario.trim() || !detalle) return

    const resultado = await addComment(postId, nuevoComentario, {
      emocionAutor: emocionComentario,
      referenciaNarrativaId: narrativa.referenciaId,
      fronteraSpoilerId: narrativa.fronteraId,
      obraCruzadaId: narrativa.obraCruzadaId,
      fronteraCruzadaId: narrativa.fronteraId,
      ...overrides,
    })

    if ('referenciaCruzadaDetectada' in resultado) {
      setDetecciones(resultado.detecciones)
      return
    }

    setDetecciones(null)
    agregarComentarioAlEstado(resultado)
  }

  async function handleComentar() {
    enviarComentario()
  }

  function handleKeyDownComentario(e: React.KeyboardEvent<HTMLInputElement>) {
    if (autocomplete.handleKeyDown(e)) return
    if (e.key === 'Enter') handleComentar()
  }

  function handleComentarioEliminado(commentId: number) {
    if (!detalle) return
    setDetalle({ ...detalle, comments: detalle.comments.filter((c) => c.id !== commentId) })
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
        <SaveButton postId={post.id} guardadoInicial={post.is_saved} />

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

        <p className={styles.text}><LinkedText text={post.text} /></p>

        {post.imagen && <img className={styles.image} src={post.imagen} alt="" />}

        <PostActions postId={post.id} reaccionInicial={detalle.post_reaction} />
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
              ref={comentarioInputRef}
              className={styles.commentInput}
              type="text"
              value={nuevoComentario}
              onChange={(e) => autocomplete.handleChange(e.target.value)}
              onFocus={() => setEmocionAbierta(true)}
              onBlur={() => {
                setTimeout(() => setEmocionAbierta(false), 150)
                setTimeout(autocomplete.cerrar, 150)
              }}
              placeholder="Escribe un comentario..."
              onKeyDown={handleKeyDownComentario}
            />
            {autocomplete.suggestions.length > 0 ? (
              <AutocompleteDropdown
                suggestions={autocomplete.suggestions}
                activeIndex={autocomplete.activeIndex}
                onSelect={autocomplete.seleccionar}
              />
            ) : (
              <EmocionPopover
                visible={emocionAbierta}
                value={emocionComentario}
                onSelect={setEmocionComentario}
              />
            )}
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
            onEliminado={handleComentarioEliminado}
          />
        ))
      )}

      {detecciones && (
        <ReferenciaCruzadaAviso
          detecciones={detecciones}
          onConfirmar={(obraCruzadaId, fronteraCruzadaId) => {
            enviarComentario({ obraCruzadaId, fronteraCruzadaId })
          }}
          onDescartar={() => {
            enviarComentario({ descartarReferenciaCruzada: true })
          }}
          onCancelar={() => setDetecciones(null)}
        />
      )}
    </div>
  )
}