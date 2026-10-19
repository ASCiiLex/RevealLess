import styles from './NarrativeLabel.module.css'

export interface NarrativeUnit {
  id: number
  nombre: string
  tipo: string
  etiqueta: string
  orden_inicio: number
  orden_fin: number
  padre?: number | null
  padre_etiqueta?: string | null
}

interface Props {
  unidad: NarrativeUnit
  prefix?: string
}

const TIPO_PREVIO = 'previo'

export default function NarrativeLabel({ unidad, prefix }: Props) {
  const esPrevio = unidad.tipo === TIPO_PREVIO

  return (
    <span className={styles.label}>
      {prefix && <span className={styles.prefix}>{prefix}</span>}

      {unidad.padre_etiqueta && (
        <>
          <span className={styles.padre}>{unidad.padre_etiqueta}</span>
          <span className={styles.separator}>›</span>
        </>
      )}

      <span className={`${styles.nombre} ${esPrevio ? styles.previo : ''}`}>{unidad.etiqueta}</span>
    </span>
  )
}