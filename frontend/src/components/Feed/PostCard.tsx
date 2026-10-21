import styles from './PostCard.module.css'
import PostActions from './PostActions'
import SaveButton from './SaveButton'
import NarrativeLabel from '../NarrativeLabel/NarrativeLabel'
import EmocionBadge from '../Emociones/EmocionBadge'
import GaleriaPost from '../Galeria/GaleriaPost'
import ReproductorVideo from '../Video/ReproductorVideo'
import VersusPersonajes from '../Comparativa/VersusPersonajes'
import { emocionHaloStyle } from '../../utils/emocionHalo'
import type { FeedPost } from '../../api/feed'

interface Props {
  post: FeedPost
}

// Proporción de reserva para fotos sin medidas guardadas.
const ANCHO_POR_DEFECTO = 900
const ALTO_POR_DEFECTO = 600

export default function PostCard({ post }: Props) {
  const imagenes = post.imagenes ?? []
  // Galería y vídeo tienen controles propios: van fuera del enlace al detalle.
  const esGaleria = imagenes.length > 1
  const video = post.video ?? null
  const medida = post.imagen_ancho && post.imagen_alto
    ? { ancho: post.imagen_ancho, alto: post.imagen_alto }
    : null

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
        {!video && !esGaleria && post.imagen && (
          // Con medidas, el hueco tiene la proporción exacta antes de cargar: el feed no salta.
          <img
            className={styles.image}
            src={post.imagen}
            alt=""
            width={medida?.ancho ?? ANCHO_POR_DEFECTO}
            height={medida?.alto ?? ALTO_POR_DEFECTO}
            style={medida ? { aspectRatio: `${medida.ancho} / ${medida.alto}` } : undefined}
            loading="lazy"
            decoding="async"
          />
        )}
      </a>

      {video && <ReproductorVideo video={video} />}
      {!video && esGaleria && <GaleriaPost imagenes={imagenes} disposicion={post.disposicion} />}

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