import styles from './FilterHeader.module.css'

interface Props {
  titulo: string
  linkHref?: string
}

export default function FilterHeader({ titulo, linkHref }: Props) {
  return (
    <div className={styles.wrapper}>
      <div>
        <a className={styles.backLink} href="/feed/">← Volver a Biblioteca</a>
        {linkHref ? (
          <a className={styles.title} href={linkHref}>{titulo}</a>
        ) : (
          <h1 className={styles.title}>{titulo}</h1>
        )}
      </div>
    </div>
  )
}