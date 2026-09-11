import { useState } from 'react'
import styles from './Lomo.module.css'
import { crearSuscripcion } from '../../api/suscripciones'

export interface LomoObra {
  id: number
  titulo: string
  slug: string
  imagen_url: string
  categorias: string[]
  progreso_pct?: number
  suscrito: boolean
}

interface Props {
  obra: LomoObra
  activa: boolean
  onSelect: (obra: LomoObra) => void
  mostrarProgreso: boolean
}

export default function Lomo({ obra, activa, onSelect, mostrarProgreso }: Props) {
  const [siguiendo, setSiguiendo] = useState(obra.suscrito)
  const [cargando, setCargando] = useState(false)

  async function handleSeguir() {
    if (siguiendo || cargando) return
    setCargando(true)
    try {
      await crearSuscripcion(obra.slug)
      setSiguiendo(true)
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className={styles.wrapper}>
      <button
        className={`${styles.lomo} ${activa ? styles.lomoActive : ''}`}
        onClick={() => onSelect(obra)}
        aria-pressed={activa}
      >
        {typeof obra.progreso_pct === 'number' && (
          <div className={styles.progressTrack}>
            <div className={styles.progressFill} style={{ width: `${obra.progreso_pct}%` }} />
          </div>
        )}
        <img className={styles.image} src={obra.imagen_url} alt="" />
        <div className={styles.overlay} />
        <span className={styles.title}>{obra.titulo}</span>
      </button>

      {mostrarProgreso && (
        <a className={styles.progressLink} href={`/narrative/progreso-react/${obra.slug}/`}>
          <span className={styles.progressIcon} aria-hidden="true">📖</span>
          <span>Progreso</span>
        </a>
      )}

      <button
        className={`${styles.followButton} ${siguiendo ? styles.followButtonActive : ''}`}
        onClick={handleSeguir}
        disabled={siguiendo || cargando}
      >
        <span className={styles.progressIcon} aria-hidden="true">{siguiendo ? '🔕' : '🔔'}</span>
        <span>{siguiendo ? 'Siguiendo' : 'Seguir'}</span>
      </button>
    </div>
  )
}