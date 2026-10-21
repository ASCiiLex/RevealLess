import styles from './PostCard.module.css'
import PostActions from './PostActions'
import SaveButton from './SaveButton'
import NarrativeLabel from '../NarrativeLabel/NarrativeLabel'
import EmocionBadge from '../Emociones/EmocionBadge'
import GaleriaPost from '../Galeria/GaleriaPost'
import VersusPersonajes from '../Comparativa/VersusPersonajes'
import { emocionHaloStyle } from '../../utils/emocionHalo'
import type { FeedPost } from '../../api/feed'

interface Props {
  post: FeedPost
}

export default function PostCard({ post }: Props) {
  const imagenes = post.imagenes ?? []
  // Una galería tiene controles propios (deslizador): va fuera del enlace al detalle.
  const esGaleria = imagenes.length > 1

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
          {post.obra_cruzada && (
            <>
              <span className={styles.cruce} aria-label="comparado con">⇄</span>
              <span>{post.obra_cruzada.titulo}</span>
              {/* Quien ve la tarjeta ya superó esta frontera: indicarla no revela nada. */}
              {post.frontera_cruzada && (
                <>
                  <span className={styles.narrativeSeparator}>·</span>
                  <NarrativeLabel unidad={post.frontera_cruzada} />
                </>
              )}
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
        </span>
      </div>

      <VersusPersonajes personajes={post.personajes_comparados ?? []} obraSlug={post.obra_slug} />

      <a className={styles.textLink} href={`/posts/${post.id}/`}>
        <p className={styles.text}>{post.text}</p>
        {!esGaleria && post.imagen && (
          // Proporción de referencia mientras carga; al llegar manda la real (height: auto en el CSS).
          <img
            className={styles.image}
            src={post.imagen}
            alt=""
            width={900}
            height={600}
            loading="lazy"
            decoding="async"
          />
        )}
      </a>

      {esGaleria && <GaleriaPost imagenes={imagenes} disposicion={post.disposicion} />}

      <PostActions
        postId={post.id}
        reaccionInicial={post.user_reaction}
        totalesIniciales={post.reacciones_totales}
      />

      <a className={styles.commentsLink} href={`/posts/${post.id}/`}>
        {post.comments_count} comentarios
      </a>
    </article>
  )
}