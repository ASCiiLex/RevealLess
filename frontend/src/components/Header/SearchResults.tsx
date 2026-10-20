import { useState } from 'react'
import styles from './SearchResults.module.css'
import type {
  ArcoBusqueda,
  CategoriaBusqueda,
  HashtagBusqueda,
  ResultadoBusqueda,
  TemaBusqueda,
  UsuarioBusqueda,
} from '../../api/buscar'
import { crearSuscripcion, eliminarSuscripcion, type Suscripcion } from '../../api/suscripciones'
import type { LomoObra } from '../Carousel/Lomo'

interface Props {
  resultado: ResultadoBusqueda
}

export default function SearchResults({ resultado }: Props) {
  const sinResultados =
    resultado.obras.length === 0 &&
    resultado.arcos.length === 0 &&
    resultado.categorias.length === 0 &&
    resultado.temas.length === 0 &&
    resultado.usuarios.length === 0 &&
    resultado.hashtags.length === 0

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
        <div>
          <div className={styles.groupLabel}>Obras</div>
          {resultado.obras.map((obra) => (
            <ObraRow key={obra.id} obra={obra} />
          ))}
        </div>
      )}

      {resultado.arcos.length > 0 && (
        <div>
          <div className={styles.groupLabel}>Arcos y temporadas</div>
          {resultado.arcos.map((arco) => (
            <ArcoRow key={arco.id} arco={arco} />
          ))}
        </div>
      )}

      {resultado.categorias.length > 0 && (
        <div>
          <div className={styles.groupLabel}>Categorías</div>
          {resultado.categorias.map((categoria) => (
            <CategoriaRow key={categoria.id} categoria={categoria} />
          ))}
        </div>
      )}

      {resultado.temas.length > 0 && (
        <div>
          <div className={styles.groupLabel}>Temas</div>
          {resultado.temas.map((tema) => (
            <TemaRow key={tema.id} tema={tema} />
          ))}
        </div>
      )}

      {resultado.usuarios.length > 0 && (
        <div>
          <div className={styles.groupLabel}>Usuarios</div>
          {resultado.usuarios.map((usuario) => (
            <UsuarioRow key={usuario.username} usuario={usuario} />
          ))}
        </div>
      )}

      {resultado.hashtags.length > 0 && (
        <div>
          <div className={styles.groupLabel}>Hashtags</div>
          {resultado.hashtags.map((hashtag) => (
            <HashtagRow key={hashtag.name} hashtag={hashtag} />
          ))}
        </div>
      )}
    </div>
  )
}

// Seguir / dejar de seguir común a obras, arcos y temas del buscador.
function useSeguimiento(suscrito: boolean, suscripcionInicial: number | null, crear: () => Promise<Suscripcion>) {
  const [siguiendo, setSiguiendo] = useState(suscrito)
  const [suscripcionId, setSuscripcionId] = useState(suscripcionInicial)
  const [cargando, setCargando] = useState(false)

  async function alternar() {
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
        const suscripcion = await crear()
        setSiguiendo(true)
        setSuscripcionId(suscripcion.id)
      }
    } finally {
      setCargando(false)
    }
  }

  return { siguiendo, cargando, alternar }
}

// Enlace y botón hermanos: un <button> dentro de un <a> no es HTML válido.
function BotonSeguir({ siguiendo, cargando, onClick }: { siguiendo: boolean; cargando: boolean; onClick: () => void }) {
  return (
    <button
      className={`${styles.followButton} ${siguiendo ? styles.followButtonActive : ''}`}
      onClick={onClick}
      disabled={cargando}
    >
      {siguiendo ? 'Siguiendo' : 'Seguir'}
    </button>
  )
}

function ObraRow({ obra }: { obra: LomoObra }) {
  const { siguiendo, cargando, alternar } = useSeguimiento(
    obra.suscrito, obra.suscripcion_id, () => crearSuscripcion(obra.slug),
  )

  return (
    <div className={styles.row}>
      <a className={styles.rowMainLink} href={`/narrative/obra/${obra.slug}/`}>
        <img className={styles.thumb} src={obra.imagen_url} alt="" loading="lazy" decoding="async" />
        <span className={styles.titulo}>{obra.titulo}</span>
      </a>
      <BotonSeguir siguiendo={siguiendo} cargando={cargando} onClick={alternar} />
    </div>
  )
}

function ArcoRow({ arco }: { arco: ArcoBusqueda }) {
  const { siguiendo, cargando, alternar } = useSeguimiento(
    arco.suscrito, arco.suscripcion_id, () => crearSuscripcion(arco.obra_slug, { unidadId: arco.id }),
  )
  const contexto = arco.padre_nombre ? `${arco.obra_titulo} · ${arco.padre_nombre}` : arco.obra_titulo

  return (
    <div className={styles.row}>
      <a className={styles.rowMainLink} href={`/feed/?unidad=${arco.id}`}>
        <span>
          <span className={styles.titulo}>{arco.nombre}</span>
          <span className={styles.subtitulo}>{contexto}</span>
        </span>
      </a>
      <BotonSeguir siguiendo={siguiendo} cargando={cargando} onClick={alternar} />
    </div>
  )
}

function CategoriaRow({ categoria }: { categoria: CategoriaBusqueda }) {
  return (
    <a className={styles.rowLink} href={`/narrative/categoria/${categoria.id}/`}>
      <span className={styles.categoriaIcono} aria-hidden="true">▦</span>
      <span>
        <span className={styles.titulo}>{categoria.nombre}</span>
        <span className={styles.subtitulo}>
          {categoria.total_obras} obra{categoria.total_obras === 1 ? '' : 's'}
        </span>
      </span>
    </a>
  )
}

function TemaRow({ tema }: { tema: TemaBusqueda }) {
  const { siguiendo, cargando, alternar } = useSeguimiento(
    tema.suscrito, tema.suscripcion_id, () => crearSuscripcion(tema.obra_slug, { temaId: tema.id }),
  )

  return (
    <div className={styles.row}>
      <a className={styles.rowMainLink} href={`/narrative/tema/${tema.id}/`}>
        <span>
          <span className={styles.titulo}>{tema.nombre}</span>
          <span className={styles.subtitulo}>{tema.obra_titulo}</span>
        </span>
      </a>
      <BotonSeguir siguiendo={siguiendo} cargando={cargando} onClick={alternar} />
    </div>
  )
}

function UsuarioRow({ usuario }: { usuario: UsuarioBusqueda }) {
  return (
    <a className={styles.rowLink} href={`/perfil/${usuario.username}/`}>
      <img className={styles.avatarThumb} src={usuario.avatar_url} alt="" loading="lazy" decoding="async" />
      <span className={styles.titulo}>@{usuario.username}</span>
    </a>
  )
}

function HashtagRow({ hashtag }: { hashtag: HashtagBusqueda }) {
  return (
    <a className={styles.rowLink} href={`/feed/?hashtag=${encodeURIComponent(hashtag.name)}`}>
      <span className={styles.titulo}>#{hashtag.name}</span>
    </a>
  )
}