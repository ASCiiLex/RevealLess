import styles from './CategoryChips.module.css'

interface Props {
  categorias: string[]
  activa: string | null
  onSelect: (categoria: string | null) => void
}

export default function CategoryChips({ categorias, activa, onSelect }: Props) {
  if (categorias.length === 0) {
    return null
  }

  return (
    <div className={styles.wrapper}>
      <button
        className={`${styles.chip} ${activa === null ? styles.chipActive : ''}`}
        onClick={() => onSelect(null)}
      >
        Todo
      </button>
      {categorias.map((cat) => (
        <button
          key={cat}
          className={`${styles.chip} ${activa === cat ? styles.chipActive : ''}`}
          onClick={() => onSelect(cat)}
        >
          {cat}
        </button>
      ))}
    </div>
  )
}