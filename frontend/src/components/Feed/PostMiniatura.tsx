import styles from './PostMiniatura.module.css'

interface Props {
  imagen: string | null
  texto: string
}

// Tesela de grid (perfil, guardados): la foto si la hay; si no, el arranque del texto.
export default function PostMiniatura({ imagen, texto }: Props) {
  if (imagen) {
    return <img className={styles.imagen} src={imagen} alt="" />
  }
  return (
    <div className={styles.texto}>
      <p>{texto}</p>
    </div>
  )
}