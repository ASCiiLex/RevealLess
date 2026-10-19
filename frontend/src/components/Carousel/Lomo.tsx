import { useEffect, useState } from 'react'
import styles from './Lomo.module.css'
import { crearSuscripcion, eliminarSuscripcion } from '../../api/suscripciones'

export interface LomoObra {
  id: number
  titulo: string
  slug: string
  imagen_url: string
  categorias: string[]
  progreso_pct?: number
  // Solo la suscripción a la obra completa (o al tema, en lomos de tema).
  suscrito: boolean
  suscripcion_id: number | null
  silenciada?: boolean
  es_tema?: boolean
  tema_id?: number | null
}

interface Props {
  obra: LomoObra
  activa: boolean
  onSelect: (obra: LomoObra) => void
  mostrarProgreso: boolean
  onCambioSuscripcion?: () => void
}

const URL_SUSCRIPCIONES = '/suscripciones/'

export default function Lomo({ obra, activa, onSelect, mostrarProgreso, onCambioSuscripcion }: Props) {
  const [siguiendo, setSiguiendo] = useState(obra.suscrito)
  const [suscripcionId, setSuscripcionId] = useState(obra.suscripcion_id)
  const [cargando, setCargando] = useState(false)

  // Tras recargar el catálogo, el estado del servidor manda sobre el local.
  useEffect(() => {
    setSiguiendo(obra.suscrito)
    setSuscripcionId(obra.suscripcion_id)
  }, [obra.suscrito, obra.suscripcion_id])

  const esTema = !!obra.es_tema

  async function handleToggleSeguir() {
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
        const suscripcion = esTema
          ? await crearSuscripcion(obra.slug, { temaId: obra.tema_id ?? undefined })
          : await crearSuscripcion(obra.slug)
        setSiguiendo(true)
        setSuscripcionId(suscripcion.id)
      }
      onCambioSuscripcion?.()
    } finally {
      setCargando(false)
    }
  }

  const hrefInfo = esTema ? `/narrative/tema/${obra.tema_id}/` : `/narrative/obra/${obra.slug}/`
  const mostrarProgresoFinal = mostrarProgreso && !esTema

  return (
    <div className={styles.wrapper}>
      {/* Contenedor visual: el botón de filtro y el enlace de info son hermanos, no anidados. */}
      <div className={`${styles.lomo} ${activa ? styles.lomoActive : ''}`}>
        <button
          type="button"
          className={styles.lomoButton}
          onClick={() => onSelect(obra)}
          aria-pressed={activa}
        >
          {!esTema && typeof obra.progreso_pct === 'number' && (
            <div className={styles.progressTrack}>
              <div className={styles.progressFill} style={{ width: `${obra.progreso_pct}%` }} />
            </div>
          )}

          {/* Las portadas fuera de la parte visible del carrusel se descargan al acercarse. */}
          <img className={styles.image} src={obra.imagen_url} alt="" loading="lazy" decoding="async" />
          <div className={styles.overlay} />
          <span className={styles.title}>{obra.titulo}</span>
        </button>

        <a
          className={styles.infoIcon}
          href={hrefInfo}
          aria-label={`Ver información de ${obra.titulo}`}
          title="Ver información"
        >
          i
        </a>
      </div>

      {mostrarProgresoFinal && (
        <a className={styles.progressLink} href={`/narrative/progreso/${obra.slug}/`}>
          <span className={styles.progressIcon} aria-hidden="true">📖</span>
          <span className={styles.actionText}>Progreso</span>
        </a>
      )}

      {/* El silencio se gestiona solo desde Suscripciones: aquí se informa, no se cambia. */}
      {obra.silenciada ? (
        <a
          className={styles.progressLink}
          href={URL_SUSCRIPCIONES}
          title="Gestionar en Suscripciones"
          aria-label={`${obra.titulo} está silenciada: gestionar en Suscripciones`}
        >
          <span className={styles.progressIcon} aria-hidden="true">🔇</span>
          <span className={styles.actionText}>Silenciada</span>
        </a>
      ) : (
        <button
          type="button"
          className={`${styles.followButton} ${siguiendo ? styles.followButtonActive : ''}`}
          onClick={handleToggleSeguir}
          disabled={cargando}
          aria-pressed={siguiendo}
          aria-label={siguiendo ? `Dejar de seguir ${obra.titulo}` : `Seguir ${obra.titulo}`}
          title={siguiendo ? 'Dejar de seguir' : 'Seguir'}
        >
          <span className={styles.followIcon} aria-hidden="true">{siguiendo ? '✓' : '+'}</span>
          <span className={styles.actionText}>{siguiendo ? 'Siguiendo' : 'Seguir'}</span>
        </button>
      )}
    </div>
  )
}