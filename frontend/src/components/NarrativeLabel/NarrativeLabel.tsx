import styles from './NarrativeLabel.module.css'
import type { NarrativeUnit } from '../../api/feed'

interface Props {
  unidad: NarrativeUnit
}

export default function NarrativeLabel({ unidad }: Props) {
  return (
    <span className={styles.label}>
      {unidad.padre_etiqueta && (
        <>
          <span className={styles.padre}>{unidad.padre_etiqueta}</span>
          <span className={styles.separator}>›</span>
        </>
      )}

      <span className={styles.nombre}>{unidad.etiqueta}</span>
    </span>
  )
}