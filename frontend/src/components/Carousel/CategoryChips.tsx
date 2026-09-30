import styles from './CategoryChips.module.css'

interface Props {
  categorias: string[]
  activas: string[]
  onToggle: (categoria: string) => void
  onLimpiar: () => void
}

// Selección múltiple: "Todo" limpia el filtro; el resto se activa y desactiva por separado.
export default function CategoryChips({ categorias, activas, onToggle, onLimpiar }: Props) {
  if (categorias.length === 0) {
    return null
  }

  return (
    <div className={styles.wrapper}>
      <button
        type="button"
        className={`${styles.chip} ${activas.length === 0 ? styles.chipActive : ''}`}
        onClick={onLimpiar}
        aria-pressed={activas.length === 0}
      >
        Todo
      </button>
      {categorias.map((cat) => {
        const activa = activas.includes(cat)
        return (
          <button
            type="button"
            key={cat}
            className={`${styles.chip} ${activa ? styles.chipActive : ''}`}
            onClick={() => onToggle(cat)}
            aria-pressed={activa}
          >
            {cat}
          </button>
        )
      })}
    </div>
  )
}