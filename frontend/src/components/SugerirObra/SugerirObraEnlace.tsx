import styles from './SugerirObra.module.css'

interface Props {
  onClick: () => void
  texto?: string
}

export default function SugerirObraEnlace({ onClick, texto = '¿No encuentras la obra? Sugiérela' }: Props) {
  return (
    // preventDefault en mousedown: el campo de búsqueda no pierde el foco ni cierra su lista.
    <button type="button" className={styles.enlace} onMouseDown={(e) => e.preventDefault()} onClick={onClick}>
      {texto}
    </button>
  )
}