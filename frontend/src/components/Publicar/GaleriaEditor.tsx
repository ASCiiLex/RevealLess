import { useRef, type PointerEvent as ReactPointerEvent } from 'react'
import styles from './GaleriaEditor.module.css'
import GaleriaPost, {
  DISPOSICIONES, ZOOM_BASE, ZOOM_MAXIMO, disposicionEfectiva, estiloEncuadre, type ImagenGaleria,
} from '../Galeria/GaleriaPost'

export interface ImagenBorrador {
  archivo: File
  etiqueta: string
  // URL local de vista previa; se revoca al quitar la imagen.
  url: string
  enfoqueX: number
  enfoqueY: number
  zoom: number
}

export type CambioEncuadre = Partial<Pick<ImagenBorrador, 'enfoqueX' | 'enfoqueY' | 'zoom'>>

interface Props {
  imagenes: ImagenBorrador[]
  disposicion: string
  onDisposicion: (disposicion: string) => void
  onEtiqueta: (indice: number, etiqueta: string) => void
  onEncuadre: (indice: number, cambio: CambioEncuadre) => void
  onQuitar: (indice: number) => void
}

const limitar = (valor: number) => Math.round(Math.min(Math.max(valor, 0), 100))

export function aGaleria(img: ImagenBorrador): ImagenGaleria {
  return { url: img.url, etiqueta: img.etiqueta.trim(), enfoque_x: img.enfoqueX, enfoque_y: img.enfoqueY, zoom: img.zoom }
}

export default function GaleriaEditor({ imagenes, disposicion, onDisposicion, onEtiqueta, onEncuadre, onQuitar }: Props) {
  const arrastre = useRef<{ indice: number; px: number; py: number; x: number; y: number; ancho: number; alto: number } | null>(null)

  if (imagenes.length === 0) return null

  const numero = imagenes.length
  const actual = disposicionEfectiva(numero, disposicion)

  function empezar(indice: number, e: ReactPointerEvent<HTMLDivElement>) {
    const { width, height } = e.currentTarget.getBoundingClientRect()
    e.currentTarget.setPointerCapture(e.pointerId)
    const img = imagenes[indice]
    arrastre.current = { indice, px: e.clientX, py: e.clientY, x: img.enfoqueX, y: img.enfoqueY, ancho: width, alto: height }
  }

  // Arrastrar a la derecha descubre la parte izquierda: el punto de enfoque se mueve al revés.
  function mover(e: ReactPointerEvent<HTMLDivElement>) {
    const a = arrastre.current
    if (!a) return
    onEncuadre(a.indice, {
      enfoqueX: limitar(a.x - ((e.clientX - a.px) / a.ancho) * 100),
      enfoqueY: limitar(a.y - ((e.clientY - a.py) / a.alto) * 100),
    })
  }

  function soltar() {
    arrastre.current = null
  }

  return (
    <div className={styles.galeria}>
      <div className={styles.miniaturas}>
        {imagenes.map((img, i) => (
          <div key={img.url} className={styles.miniatura}>
            <div
              className={styles.marco}
              onPointerDown={(e) => empezar(i, e)}
              onPointerMove={mover}
              onPointerUp={soltar}
              onPointerCancel={soltar}
              title="Arrastra para encuadrar"
            >
              <img src={img.url} alt="" draggable={false} style={estiloEncuadre(aGaleria(img))} />
              <button
                type="button"
                className={styles.quitar}
                onPointerDown={(e) => e.stopPropagation()}
                onClick={() => onQuitar(i)}
                aria-label={`Quitar imagen ${i + 1}`}
              >
                ×
              </button>
            </div>
            {numero > 1 && (
              <>
                <label className={styles.zoom}>
                  <span>Zoom</span>
                  <input
                    type="range"
                    min={ZOOM_BASE}
                    max={ZOOM_MAXIMO}
                    step={5}
                    value={img.zoom}
                    onChange={(e) => onEncuadre(i, { zoom: Number(e.target.value) })}
                    aria-label={`Zoom de la imagen ${i + 1}`}
                  />
                </label>
                <input
                  className={styles.etiqueta}
                  value={img.etiqueta}
                  maxLength={40}
                  placeholder="Etiqueta (ej. Anime)"
                  aria-label={`Etiqueta de la imagen ${i + 1}`}
                  onChange={(e) => onEtiqueta(i, e.target.value)}
                />
              </>
            )}
          </div>
        ))}
      </div>

      {numero > 1 && (
        <>
          <span className={styles.titulo}>Arrastra cada miniatura para encuadrarla.</span>
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
          <GaleriaPost imagenes={imagenes.map(aGaleria)} disposicion={actual} />
        </>
      )}
    </div>
  )
}