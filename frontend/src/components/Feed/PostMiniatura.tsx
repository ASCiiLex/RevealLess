import styles from './PostMiniatura.module.css'
import { disposicionEfectiva, estiloEncuadre, type ImagenGaleria } from '../Galeria/GaleriaPost'

interface Props {
  imagenes: ImagenGaleria[]
  disposicion?: string | null
  texto: string
}

// Tesela de grid (perfil, guardados): la composición del post, estática; sin fotos, el arranque del texto.
export default function PostMiniatura({ imagenes, disposicion, texto }: Props) {
  if (imagenes.length === 0) {
    return (
      <div className={styles.texto}>
        <p>{texto}</p>
      </div>
    )
  }

  if (imagenes.length === 1) {
    return (
      <img
        className={styles.imagen}
        src={imagenes[0].url}
        alt=""
        loading="lazy"
        decoding="async"
        style={estiloEncuadre(imagenes[0])}
      />
    )
  }

  // En una tesela que es un enlace no cabe el deslizador: se muestra partido en dos.
  const tipo = disposicionEfectiva(imagenes.length, disposicion)
  const clase = tipo === 'deslizador' ? 'lado' : tipo

  return (
    <div className={`${styles.composicion} ${styles[clase] ?? ''}`}>
      {imagenes.map((img, i) => (
        <div
          key={`${img.url}-${i}`}
          className={styles.celda}
          // La destacada ocupa todas las filas de la columna izquierda.
          style={clase === 'destacada' && i === 0 ? { gridRow: `span ${imagenes.length - 1}` } : undefined}
        >
          <img src={img.url} alt="" loading="lazy" decoding="async" style={estiloEncuadre(img)} />
        </div>
      ))}
    </div>
  )
}