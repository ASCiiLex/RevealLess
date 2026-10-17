import { useEffect, useState } from 'react'
import styles from './PostDetailView.module.css'
import CommentItem from './CommentItem'
import ComentarioForm from './ComentarioForm'
import EditPostForm from './EditPostForm'
import PostActions from '../Feed/PostActions'
import SaveButton from '../Feed/SaveButton'
import LinkedText from '../Text/LinkedText'
import NarrativeLabel from '../NarrativeLabel/NarrativeLabel'
import EmocionBadge from '../Emociones/EmocionBadge'
import GaleriaPost from '../Galeria/GaleriaPost'
import VersusPersonajes from '../Comparativa/VersusPersonajes'
import { emocionHaloStyle } from '../../utils/emocionHalo'
import { fetchPostDetail, type PostDetail } from '../../api/postDetail'
import type { CommentItem as CommentItemType } from '../../api/comentarios'
import { fetchObraDetalle, type ObraDetalle } from '../../api/suscripciones'
import type { FeedPost } from '../../api/feed'

interface Props {
  postId: number
}

export default function PostDetailView({ postId }: Props) {
  const [detalle, setDetalle] = useState<PostDetail | null>(null)
  const [obraDetalle, setObraDetalle] = useState<ObraDetalle | null>(null)
  const [editando, setEditando] = useState(false)

  useEffect(() => {
    fetchPostDetail(postId).then(setDetalle)
  }, [postId])

  const obraSlug = detalle?.post.obra_slug
  useEffect(() => {
    if (obraSlug) fetchObraDetalle(obraSlug).then(setObraDetalle)
  }, [obraSlug])

  function handleComentarioCreado(comentario: CommentItemType) {
    setDetalle((prev) => prev && { ...prev, comments: [comentario, ...prev.comments] })
  }

  function handleComentarioEliminado(commentId: number) {
    setDetalle((prev) => prev && { ...prev, comments: prev.comments.filter((c) => c.id !== commentId) })
  }

  function handlePostActualizado(postActualizado: FeedPost) {
    setDetalle((prev) => prev && { ...prev, post: postActualizado })
    setEditando(false)
  }

  if (!detalle) {
    return null
  }

  const { post, comments } = detalle
  const perfilUrl = `/perfil/${encodeURIComponent(post.autor)}/`
  const imagenes = post.imagenes ?? (post.imagen ? [{ url: post.imagen, etiqueta: '' }] : [])

  return (
    <div className={styles.wrapper}>
      <div className={styles.postCard} style={emocionHaloStyle(post.emocion_autor)}>
        {!post.is_own_post && <SaveButton postId={post.id} guardadoInicial={post.is_saved} />}
        {post.is_own_post && (
          <button className={styles.editButton} onClick={() => setEditando(true)}>
            Editar
          </button>
        )}

        <div className={styles.meta}>
          {/* Fuera del tabulador: el @usuario ya enlaza al mismo perfil. */}
          <a className={styles.avatarLink} href={perfilUrl} tabIndex={-1} aria-hidden="true">
            <img className={styles.avatar} src={post.autor_avatar} alt="" />
          </a>

          <div className={styles.authorRow}>
            <div>
              <div className={styles.author}>
                <a className={styles.authorLink} href={perfilUrl}>@{post.autor}</a>{' '}
                <EmocionBadge emocionAutor={post.emocion_autor} />
              </div>

              <div className={styles.obra}>
                <span>{post.obra_titulo}</span>
                {post.obra_cruzada && (
                  <>
                    <span className={styles.cruce} aria-label="comparado con">⇄</span>
                    <span>{post.obra_cruzada.titulo}</span>
                  </>
                )}
                {post.referencia_narrativa && (
                  <>
                    <span className={styles.narrativeSeparator}>|</span>
                    <NarrativeLabel unidad={post.referencia_narrativa} />
                  </>
                )}
                {(post.temas ?? []).map((t) => (
                  <a key={t.id} className={styles.tema} href={`/narrative/tema/${t.id}/`}>#{t.nombre}</a>
                ))}
              </div>
            </div>
          </div>
        </div>

        <VersusPersonajes personajes={post.personajes_comparados ?? []} obraSlug={post.obra_slug} />

        <p className={styles.text}><LinkedText text={post.text} /></p>

        <GaleriaPost imagenes={imagenes} disposicion={post.disposicion} />

        <PostActions
          postId={post.id}
          reaccionInicial={detalle.post_reaction}
          totalesIniciales={post.reacciones_totales}
        />
      </div>

      {editando && (
        <EditPostForm
          post={post}
          onGuardado={handlePostActualizado}
          onCancelar={() => setEditando(false)}
        />
      )}

      <h2 className={styles.commentsTitle}>Comentarios ({comments.length})</h2>

      <ComentarioForm
        postId={postId}
        obraDetalle={obraDetalle}
        variante="comentario"
        onCreado={handleComentarioCreado}
      />

      {comments.length === 0 ? (
        <p className={styles.empty}>No hay comentarios todavía.</p>
      ) : (
        comments.map((c) => (
          <CommentItem
            key={c.id}
            comment={c}
            postId={postId}
            obraDetalle={obraDetalle}
            onEliminado={handleComentarioEliminado}
          />
        ))
      )}
    </div>
  )
}