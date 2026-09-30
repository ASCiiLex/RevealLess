import styles from './CategoryChips.module.css'

export type EstadoChip = 'o' | 'y'

interface Props {
  categorias: string[]
  estados: Record<string, EstadoChip>
  onCiclar: (categoria: string) => void
  onLimpiar: () => void
}

const DESCRIPCION: Record<EstadoChip, string> = {
  o: 'opcional (O)',
  y: 'obligatoria (Y)',
}

// Cada pulsación cicla: inactivo → O → Y → inactivo. "Todo" limpia el filtro.
export default function CategoryChips({ categorias, estados, onCiclar, onLimpiar }: Props) {
  if (categorias.length === 0) {
    return null
  }

  const hayFiltro = Object.keys(estados).length > 0

  return (
    <div className={styles.contenedor}>
      <div className={styles.wrapper}>
        <button
          type="button"
          className={`${styles.chip} ${hayFiltro ? '' : styles.chipY}`}
          onClick={onLimpiar}
          aria-pressed={!hayFiltro}
        >
          Todo
        </button>
        {categorias.map((cat) => {
          const estado = estados[cat]
          const clase = estado === 'y' ? styles.chipY : estado === 'o' ? styles.chipO : ''
          return (
            <button
              type="button"
              key={cat}
              className={`${styles.chip} ${clase}`}
              onClick={() => onCiclar(cat)}
              aria-label={estado ? `${cat}: ${DESCRIPCION[estado]}` : `${cat}: sin filtrar`}
              title={estado ? DESCRIPCION[estado] : undefined}
            >
              {estado && (
                <span className={styles.marca} aria-hidden="true">
                  {estado === 'y' ? 'Y' : 'O'}
                </span>
              )}
              {cat}
            </button>
          )
        })}
      </div>
      {hayFiltro && (
        <p className={styles.ayuda}>
          O: cualquiera de ellas · Y: obligatoria · pulsa de nuevo un chip para cambiarlo
        </p>
      )}
    </div>
  )
}