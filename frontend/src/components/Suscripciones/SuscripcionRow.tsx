import { useState } from 'react'
import styles from './SuscripcionRow.module.css'
import { toggleActivaSuscripcion, type Suscripcion } from '../../api/suscripciones'

interface Props {
  suscripcion: Suscripcion
  onRemove: (id: number) => void
}

function etiquetaNivel(s: Suscripcion): string {
  if (s.nivel === 'personaje') return 'Personaje'
  if (s.nivel === 'unidad' && s.unidad) return `Arco: ${s.unidad.etiqueta}`
  if (s.nivel === 'tema' && s.tema) return `Tema: ${s.tema.nombre}`
  return 'Obra completa'
}

// Un personaje no tiene obra: se muestra el propio personaje.
function objetivo(s: Suscripcion) {
  if (s.personaje) {
    return { titulo: s.personaje.nombre, imagen: s.personaje.imagen_url, redonda: true }
  }
  return { titulo: s.obra?.titulo ?? '', imagen: s.obra?.imagen_url ?? '', redonda: false }
}

export default function SuscripcionRow({ suscripcion, onRemove }: Props) {
  const [activa, setActiva] = useState(suscripcion.activa)
  const [cargando, setCargando] = useState(false)
  const { titulo, imagen, redonda } = objetivo(suscripcion)

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
        <img className={`${styles.thumb} ${redonda ? styles.thumbRedonda : ''}`} src={imagen} alt="" />
        <div>
          <div className={styles.titulo}>{titulo}</div>
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
          aria-label={`Dejar de seguir ${titulo}`}
        >
          ✕
        </button>
      </div>
    </div>
  )
}
