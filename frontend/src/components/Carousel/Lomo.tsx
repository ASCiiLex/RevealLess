import { useEffect, useState } from 'react'
import styles from './Lomo.module.css'
import {
  crearSuscripcion,
  crearSuscripcionPersonaje,
  eliminarSuscripcion,
  toggleActivaSuscripcion,
} from '../../api/suscripciones'

export interface LomoObra {
  id: number
  // Única entre tipos (obra-1, tema-2, personaje-3): key de React.
  clave: string
  titulo: string
  slug: string
  imagen_url: string
  categorias: string[]
  progreso_pct?: number
  // Solo la suscripción a la obra completa, al tema o al personaje del lomo.
  suscrito: boolean
  suscripcion_id: number | null
  silenciada?: boolean
  es_tema?: boolean
  tema_id?: number | null
  es_personaje?: boolean
  personaje_id?: number | null
}

interface Props {
  obra: LomoObra
  activa: boolean
  onSelect: (obra: LomoObra) => void
  mostrarProgreso: boolean
  onCambioSuscripcion?: () => void
}

type EstadoSeguimiento = 'ninguno' | 'activa' | 'silenciada'

// Ciclo del botón: + → ✓ → silenciada → +. Si se pasa, basta con seguir pulsando.
const PRESENTACION: Record<EstadoSeguimiento, { texto: string; accion: string }> = {
  ninguno: { texto: 'Seguir', accion: 'Seguir' },
  activa: { texto: 'Siguiendo', accion: 'Silenciar' },
  silenciada: { texto: 'Silenciada', accion: 'Dejar de seguir' },
}

// Tamaño del lomo en escritorio: reserva el hueco antes de cargar; el CSS lo ajusta en móvil.
const ANCHO_LOMO = 130
const ALTO_LOMO = 190

function estadoInicial(obra: LomoObra): EstadoSeguimiento {
  if (obra.silenciada) return 'silenciada'
  return obra.suscrito ? 'activa' : 'ninguno'
}

function IconoSilencio() {
  return (
    <svg
      className={styles.iconoSilencio}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M4 9h4l5-4v14l-5-4H4z" />
      <path d="M17 9l5 6M22 9l-5 6" />
    </svg>
  )
}

export default function Lomo({ obra, activa, onSelect, mostrarProgreso, onCambioSuscripcion }: Props) {
  const [estado, setEstado] = useState<EstadoSeguimiento>(() => estadoInicial(obra))
  const [suscripcionId, setSuscripcionId] = useState(obra.suscripcion_id)
  const [cargando, setCargando] = useState(false)

  // Tras recargar el catálogo, el estado del servidor manda sobre el local.
  useEffect(() => {
    setEstado(estadoInicial(obra))
    setSuscripcionId(obra.suscripcion_id)
  }, [obra.suscrito, obra.silenciada, obra.suscripcion_id])

  const esTema = !!obra.es_tema
  const esPersonaje = !!obra.es_personaje

  function crear() {
    if (esPersonaje) return crearSuscripcionPersonaje(obra.personaje_id ?? obra.id)
    if (esTema) return crearSuscripcion(obra.slug, { temaId: obra.tema_id ?? undefined })
    return crearSuscripcion(obra.slug)
  }

  async function handleCiclo() {
    if (cargando) return
    setCargando(true)
    try {
      if (estado === 'ninguno') {
        const suscripcion = await crear()
        setSuscripcionId(suscripcion.id)
        setEstado('activa')
      } else if (suscripcionId === null) {
        setEstado('ninguno')
      } else if (estado === 'activa') {
        await toggleActivaSuscripcion(suscripcionId, false)
        setEstado('silenciada')
      } else {
        await eliminarSuscripcion(suscripcionId)
        setSuscripcionId(null)
        setEstado('ninguno')
      }
      onCambioSuscripcion?.()
    } finally {
      setCargando(false)
    }
  }

  const hrefInfo = esPersonaje
    ? `/narrative/personaje/${obra.personaje_id}/`
    : esTema
      ? `/narrative/tema/${obra.tema_id}/`
      : `/narrative/obra/${obra.slug}/`
  const esObra = !esTema && !esPersonaje
  const mostrarProgresoFinal = mostrarProgreso && esObra
  const { texto, accion } = PRESENTACION[estado]
  const claseEstado =
    estado === 'activa'
      ? styles.followButtonActive
      : estado === 'silenciada'
        ? styles.followButtonSilenciada
        : ''

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
          {esObra && typeof obra.progreso_pct === 'number' && (
            <div className={styles.progressTrack}>
              <div className={styles.progressFill} style={{ width: `${obra.progreso_pct}%` }} />
            </div>
          )}

          {/* Las portadas fuera de la parte visible del carrusel se descargan al acercarse. */}
          <img
            className={styles.image}
            src={obra.imagen_url}
            alt=""
            width={ANCHO_LOMO}
            height={ALTO_LOMO}
            loading="lazy"
            decoding="async"
          />
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

      <button
        type="button"
        className={`${styles.followButton} ${claseEstado}`}
        onClick={handleCiclo}
        disabled={cargando}
        aria-label={`${texto}: ${obra.titulo}. Pulsa para ${accion.toLowerCase()}`}
        title={`${texto} · pulsa para ${accion.toLowerCase()}`}
      >
        <span className={styles.followIcon} aria-hidden="true">
          {estado === 'silenciada' ? <IconoSilencio /> : estado === 'activa' ? '✓' : '+'}
        </span>
        <span className={styles.actionText}>{texto}</span>
      </button>
    </div>
  )
}