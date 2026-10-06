import styles from './GaleriaEditor.module.css'
import GaleriaPost, { DISPOSICIONES, disposicionEfectiva } from '../Galeria/GaleriaPost'

export interface ImagenBorrador {
  archivo: File
  etiqueta: string
  // URL local de vista previa; se revoca al quitar la imagen.
  url: string
}

interface Props {
  imagenes: ImagenBorrador[]
  disposicion: string
  onDisposicion: (disposicion: string) => void
  onEtiqueta: (indice: number, etiqueta: string) => void
  onQuitar: (indice: number) => void
}

export default function GaleriaEditor({ imagenes, disposicion, onDisposicion, onEtiqueta, onQuitar }: Props) {
  if (imagenes.length === 0) return null

  const numero = imagenes.length
  const actual = disposicionEfectiva(numero, disposicion)

  return (
    <div className={styles.galeria}>
      <div className={styles.miniaturas}>
        {imagenes.map((img, i) => (
          <div key={img.url} className={styles.miniatura}>
            <div className={styles.marco}>
              <img src={img.url} alt="" />
              <button
                type="button"
                className={styles.quitar}
                onClick={() => onQuitar(i)}
                aria-label={`Quitar imagen ${i + 1}`}
              >
                ×
              </button>
            </div>
            {numero > 1 && (
              <input
                className={styles.etiqueta}
                value={img.etiqueta}
                maxLength={40}
                placeholder="Etiqueta (ej. Anime)"
                aria-label={`Etiqueta de la imagen ${i + 1}`}
                onChange={(e) => onEtiqueta(i, e.target.value)}
              />
            )}
          </div>
        ))}
      </div>

      {numero > 1 && (
        <>
          <div className={styles.disposiciones} role="radiogroup" aria-label="Disposición de las imágenes">
            {DISPOSICIONES[numero].map((o) => (
              <button
                key={o.valor}
                type="button"
                role="radio"
                aria-checked={o.valor === actual}
                className={`${styles.opcion} ${o.valor === actual ? styles.opcionActiva : ''}`}
                onClick={() => onDisposicion(o.valor)}
              >
                {o.etiqueta}
              </button>
            ))}
          </div>
          <span className={styles.titulo}>Vista previa</span>
          <GaleriaPost
            imagenes={imagenes.map((img) => ({ url: img.url, etiqueta: img.etiqueta.trim() }))}
            disposicion={actual}
          />
        </>
      )}
    </div>
  )
}