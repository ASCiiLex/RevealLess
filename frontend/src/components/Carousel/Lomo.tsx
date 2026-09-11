import styles from './Lomo.module.css'

export interface LomoObra {
  id: number
  titulo: string
  slug: string
  imagen_url: string
  categorias: string[]
  progreso_pct?: number
}

interface Props {
  obra: LomoObra
  activa: boolean
  onSelect: (obra: LomoObra) => void
  mostrarProgreso: boolean
}

export default function Lomo({ obra, activa, onSelect, mostrarProgreso }: Props) {
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
    </div>
  )
}