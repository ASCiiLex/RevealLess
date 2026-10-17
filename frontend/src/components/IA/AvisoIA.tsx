import styles from './AvisoIA.module.css'

interface Props {
  certeza: number
  fiable: boolean
  /** Momento en que el autor da el visto bueno: cambia el final del texto. */
  accion: 'publicar' | 'confirmar'
  /** Fondo sobre el que se pinta: el formulario (oscuro) o un modal (claro). */
  superficie?: 'oscura' | 'clara'
}

/** Aviso destacado de toda propuesta de la IA: el autor tiene que comprobarla antes de darla por buena. */
export default function AvisoIA({ certeza, fiable, accion, superficie = 'oscura' }: Props) {
  return (
    <div
      className={`${styles.aviso} ${fiable ? styles.revisar : styles.baja} ${styles[superficie]}`}
      role="status"
    >
      <span className={styles.icono} aria-hidden="true">⚠</span>
      <div>
        <strong className={styles.titulo}>
          {fiable ? 'Revisa la frontera propuesta por la IA' : 'La IA no está segura de esta frontera'}
        </strong>
        <span className={styles.texto}>
          {fiable
            ? `Certeza ${certeza} %. Si se queda corta, será un spoiler para quien vaya por detrás. Compruébala antes de ${accion}.`
            : `Certeza baja (${certeza} %). Comprueba el episodio o capítulo antes de ${accion}.`}
        </span>
      </div>
    </div>
  )
}