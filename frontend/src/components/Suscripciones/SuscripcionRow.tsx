import { useState } from 'react'
import styles from './SuscripcionRow.module.css'
import { toggleActivaSuscripcion, type Suscripcion } from '../../api/suscripciones'

interface Props {
  suscripcion: Suscripcion
  onRemove: (id: number) => void
}

function etiquetaNivel(s: Suscripcion): string {
  if (s.nivel === 'unidad' && s.unidad) return `Arco: ${s.unidad.etiqueta}`
  if (s.nivel === 'tema' && s.tema) return `Tema: ${s.tema.nombre}`
  return 'Obra completa'
}

export default function SuscripcionRow({ suscripcion, onRemove }: Props) {
  const [activa, setActiva] = useState(suscripcion.activa)
  const [cargando, setCargando] = useState(false)

  const noLeidosTexto = activa
    ? suscripcion.no_leidos > 0
      ? `${suscripcion.no_leidos} sin leer`
      : 'sin nuevos'
    : 'silenciada'

  async function handleToggleSilencio() {
    if (cargando) return
    setCargando(true)
    try {
      const actualizada = await toggleActivaSuscripcion(suscripcion.id, !activa)
      setActiva(actualizada.activa)
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className={styles.row}>
      <div className={styles.left}>
        <img className={styles.thumb} src={suscripcion.obra.imagen_url} alt="" />
        <div>
          <div className={styles.titulo}>{suscripcion.obra.titulo}</div>
          <div className={styles.detalle}>
            {etiquetaNivel(suscripcion)} · {noLeidosTexto}
          </div>
        </div>
      </div>
      <div className={styles.actions}>
        <button
          className={`${styles.silenceButton} ${!activa ? styles.silenceButtonActive : ''}`}
          onClick={handleToggleSilencio}
          disabled={cargando}
          aria-label={activa ? 'Silenciar' : 'Reactivar'}
          title={activa ? 'Silenciar' : 'Reactivar'}
        >
          {activa ? '🔔' : '🔕'}
        </button>
        <button
          className={styles.removeButton}
          onClick={() => onRemove(suscripcion.id)}
          aria-label={`Dejar de seguir ${suscripcion.obra.titulo}`}
        >
          ✕
        </button>
      </div>
    </div>
  )
}