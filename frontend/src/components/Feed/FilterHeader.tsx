import styles from './FilterHeader.module.css'

interface Props {
  titulo: string
}

export default function FilterHeader({ titulo }: Props) {
  return (
    <div className={styles.wrapper}>
      <div>
        <a className={styles.backLink} href="/feed/react/">← Volver a Biblioteca</a>
        <h1 className={styles.title}>{titulo}</h1>
      </div>
    </div>
  )
}