import styles from './SuscripcionRow.module.css'
import type { Suscripcion } from '../../api/suscripciones'

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
  const noLeidosTexto =
    suscripcion.no_leidos > 0 ? `${suscripcion.no_leidos} sin leer` : 'sin nuevos'

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
      <button
        className={styles.removeButton}
        onClick={() => onRemove(suscripcion.id)}
        aria-label={`Dejar de seguir ${suscripcion.obra.titulo}`}
      >
        ✕
      </button>
    </div>
  )
}