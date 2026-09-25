import styles from './FilterHeader.module.css'

interface Props {
  titulo: string
  obraSlug?: string
}

export default function FilterHeader({ titulo, obraSlug }: Props) {
  return (
    <div className={styles.wrapper}>
      <div>
        <a className={styles.backLink} href="/feed/react/">← Volver a Biblioteca</a>
        {obraSlug ? (
          <a className={styles.title} href={`/narrative/obra/${obraSlug}/`}>{titulo}</a>
        ) : (
          <h1 className={styles.title}>{titulo}</h1>
        )}
      </div>
    </div>
  )
}