import styles from './PasoPost.module.css'
import BuscadorLocal, { type BuscadorItem } from './BuscadorLocal'
import type { Seleccion } from './SelectorParteTema'

interface Props {
  id: string
  etiqueta: string
  seleccion: Seleccion
  onChange: (seleccion: Seleccion) => void
  placeholder: string
  emptyLabel?: string
  buscar: (q: string) => Promise<BuscadorItem[]>
  hint?: string
}

export default function CampoSeleccion({ id, etiqueta, seleccion, onChange, placeholder, emptyLabel, buscar, hint }: Props) {
  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor={id}>{etiqueta}</label>
      <BuscadorLocal
        id={id}
        value={seleccion.id}
        valueLabel={seleccion.label}
        onChange={(nuevoId, label) => onChange({ id: nuevoId, label })}
        placeholder={placeholder}
        emptyLabel={emptyLabel}
        buscar={buscar}
      />
      {hint && <span className={styles.hint}>{hint}</span>}
    </div>
  )
}