import { useState } from 'react'
import styles from './SearchResults.module.css'
import type { ResultadoBusqueda, TemaBusqueda, UsuarioBusqueda, HashtagBusqueda, PostBusqueda } from '../../api/buscar'
import { crearSuscripcion, eliminarSuscripcion } from '../../api/suscripciones'
import type { LomoObra } from '../Carousel/Lomo'

interface Props {
  resultado: ResultadoBusqueda
}

export default function SearchResults({ resultado }: Props) {
  const sinResultados =
    resultado.obras.length === 0 &&
    resultado.temas.length === 0 &&
    resultado.usuarios.length === 0 &&
    resultado.hashtags.length === 0 &&
    resultado.posts.length === 0

  if (sinResultados) {
    return (
      <div className={styles.dropdown}>
        <p className={styles.empty}>Sin resultados.</p>
      </div>
    )
  }

  return (
    <div className={styles.dropdown}>
      {resultado.obras.length > 0 && (
        <>
          <div className={styles.groupLabel}>Obras</div>
          {resultado.obras.map((obra) => (
            <ObraRow key={obra.id} obra={obra} />
          ))}
        </>
      )}

      {resultado.temas.length > 0 && (
        <>
          <div className={styles.groupLabel}>Temas</div>
          {resultado.temas.map((tema) => (
            <TemaRow key={tema.id} tema={tema} />
          ))}
        </>
      )}

      {resultado.usuarios.length > 0 && (
        <>
          <div className={styles.groupLabel}>Usuarios</div>
          {resultado.usuarios.map((usuario) => (
            <UsuarioRow key={usuario.username} usuario={usuario} />
          ))}
        </>
      )}

      {resultado.hashtags.length > 0 && (
        <>
          <div className={styles.groupLabel}>Hashtags</div>
          {resultado.hashtags.map((hashtag) => (
            <HashtagRow key={hashtag.name} hashtag={hashtag} />
          ))}
        </>
      )}

      {resultado.posts.length > 0 && (
        <>
          <div className={styles.groupLabel}>Posts</div>
          {resultado.posts.map((post) => (
            <PostRow key={post.id} post={post} />
          ))}
        </>
      )}
    </div>
  )
}

function ObraRow({ obra }: { obra: LomoObra }) {
  const [siguiendo, setSiguiendo] = useState(obra.suscrito)
  const [suscripcionId, setSuscripcionId] = useState(obra.suscripcion_id)
  const [cargando, setCargando] = useState(false)

  async function handleToggle() {
    if (cargando) return
    setCargando(true)
    try {
      if (siguiendo) {
        if (suscripcionId !== null) {
          await eliminarSuscripcion(suscripcionId)
        }
        setSiguiendo(false)
        setSuscripcionId(null)
      } else {
        const suscripcion = await crearSuscripcion(obra.slug)
        setSiguiendo(true)
        setSuscripcionId(suscripcion.id)
      }
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className={styles.row}>
      <div className={styles.rowMain}>
        <img className={styles.thumb} src={obra.imagen_url} alt="" />
        <span className={styles.titulo}>{obra.titulo}</span>
      </div>
      <button
        className={`${styles.followButton} ${siguiendo ? styles.followButtonActive : ''}`}
        onClick={handleToggle}
        disabled={cargando}
      >
        {siguiendo ? 'Siguiendo' : 'Seguir'}
      </button>
    </div>
  )
}

function TemaRow({ tema }: { tema: TemaBusqueda }) {
  const [suscripcionId, setSuscripcionId] = useState<number | null>(null)
  const [siguiendo, setSiguiendo] = useState(false)
  const [cargando, setCargando] = useState(false)

  async function handleToggle() {
    if (cargando) return
    setCargando(true)
    try {
      if (siguiendo) {
        if (suscripcionId !== null) {
          await eliminarSuscripcion(suscripcionId)
        }
        setSiguiendo(false)
        setSuscripcionId(null)
      } else {
        const suscripcion = await crearSuscripcion(tema.obra_slug, { temaId: tema.id })
        setSiguiendo(true)
        setSuscripcionId(suscripcion.id)
      }
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className={styles.row}>
      <div className={styles.rowMain}>
        <div>
          <div className={styles.titulo}>{tema.nombre}</div>
          <div className={styles.subtitulo}>{tema.obra_titulo}</div>
        </div>
      </div>
      <button
        className={`${styles.followButton} ${siguiendo ? styles.followButtonActive : ''}`}
        onClick={handleToggle}
        disabled={cargando}
      >
        {siguiendo ? 'Siguiendo' : 'Seguir'}
      </button>
    </div>
  )
}

function UsuarioRow({ usuario }: { usuario: UsuarioBusqueda }) {
  return (
    <a className={styles.rowLink} href={`/perfil/${usuario.username}/`}>
      <img className={styles.avatarThumb} src={usuario.avatar_url} alt="" />
      <span className={styles.titulo}>@{usuario.username}</span>
    </a>
  )
}

function HashtagRow({ hashtag }: { hashtag: HashtagBusqueda }) {
  return (
    <a className={styles.rowLink} href={`/posts/hashtag/${hashtag.name}/`}>
      <span className={styles.titulo}>#{hashtag.name}</span>
    </a>
  )
}

function PostRow({ post }: { post: PostBusqueda }) {
  return (
    <a className={styles.rowLink} href={`/posts/${post.id}/`}>
      <img className={styles.thumb} src={post.image} alt="" />
      <span className={styles.postText}>{post.text}</span>
    </a>
  )
}