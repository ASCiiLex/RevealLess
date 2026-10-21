import { useState, type CSSProperties } from 'react'
import styles from './GaleriaPost.module.css'

export interface ImagenGaleria {
  url: string
  etiqueta: string
  enfoque_x?: number
  enfoque_y?: number
  zoom?: number
}

interface Props {
  imagenes: ImagenGaleria[]
  disposicion?: string | null
}

export const MAX_IMAGENES = 4
export const ZOOM_BASE = 100
export const ZOOM_MAXIMO = 300
// Dimensiones de referencia: reservan el hueco antes de cargar; el tamaño real lo fija el CSS.
const ANCHO_REFERENCIA = 900
const ALTO_REFERENCIA = 600

// Mismas claves que Post.DISPOSICIONES_POR_NUMERO; la primera es la de por defecto.
export const DISPOSICIONES: Record<number, { valor: string; etiqueta: string }[]> = {
  2: [
    { valor: 'lado', etiqueta: 'Lado a lado' },
    { valor: 'apiladas', etiqueta: 'Apiladas' },
    { valor: 'deslizador', etiqueta: 'Antes / después' },
  ],
  3: [
    { valor: 'destacada', etiqueta: '1 grande + 2' },
    { valor: 'fila', etiqueta: 'En fila' },
  ],
  4: [
    { valor: 'cuadricula', etiqueta: 'Cuadrícula' },
    { valor: 'destacada', etiqueta: '1 grande + 3' },
  ],
}

export function disposicionEfectiva(numero: number, disposicion?: string | null): string {
  const opciones = DISPOSICIONES[numero] ?? []
  const valida = opciones.find((o) => o.valor === disposicion)
  return valida?.valor ?? opciones[0]?.valor ?? ''
}

// Encuadre elegido por el autor: punto visible y zoom anclado en ese punto.
export function estiloEncuadre(img: ImagenGaleria): CSSProperties {
  const x = img.enfoque_x ?? 50
  const y = img.enfoque_y ?? 50
  const escala = (img.zoom ?? ZOOM_BASE) / 100
  return {
    objectPosition: `${x}% ${y}%`,
    transformOrigin: `${x}% ${y}%`,
    transform: escala !== 1 ? `scale(${escala})` : undefined,
  }
}

function Deslizador({ antes, despues }: { antes: ImagenGaleria; despues: ImagenGaleria }) {
  const [posicion, setPosicion] = useState(50)
  return (
    <div className={styles.deslizador}>
      <div className={styles.capaRecorte}>
        <img
          className={styles.capa}
          src={despues.url}
          alt={despues.etiqueta}
          width={ANCHO_REFERENCIA}
          height={ALTO_REFERENCIA}
          loading="lazy"
          decoding="async"
          style={estiloEncuadre(despues)}
        />
      </div>
      {/* El recorte va en el contenedor: así el zoom de la imagen no desplaza la línea. */}
      <div className={styles.capaRecorte} style={{ clipPath: `inset(0 ${100 - posicion}% 0 0)` }}>
        <img
          className={styles.capa}
          src={antes.url}
          alt={antes.etiqueta}
          width={ANCHO_REFERENCIA}
          height={ALTO_REFERENCIA}
          loading="lazy"
          decoding="async"
          style={estiloEncuadre(antes)}
        />
      </div>
      <span className={styles.linea} style={{ left: `${posicion}%` }} aria-hidden="true" />
      {antes.etiqueta && <span className={`${styles.etiqueta} ${styles.etiquetaIzq}`}>{antes.etiqueta}</span>}
      {despues.etiqueta && <span className={`${styles.etiqueta} ${styles.etiquetaDer}`}>{despues.etiqueta}</span>}
      <input
        type="range"
        className={styles.control}
        min={0}
        max={100}
        value={posicion}
        onChange={(e) => setPosicion(Number(e.target.value))}
        aria-label={`Comparar ${antes.etiqueta || 'imagen 1'} con ${despues.etiqueta || 'imagen 2'}`}
      />
    </div>
  )
}

export default function GaleriaPost({ imagenes, disposicion }: Props) {
  if (imagenes.length === 0) return null
  if (imagenes.length === 1) {
    return (
      <img
        className={styles.unica}
        src={imagenes[0].url}
        alt={imagenes[0].etiqueta}
        width={ANCHO_REFERENCIA}
        height={ALTO_REFERENCIA}
        loading="lazy"
        decoding="async"
      />
    )
  }

  const tipo = disposicionEfectiva(imagenes.length, disposicion)
  if (tipo === 'deslizador') return <Deslizador antes={imagenes[0]} despues={imagenes[1]} />

  return (
    <div className={`${styles.galeria} ${styles[tipo] ?? ''}`}>
      {imagenes.map((img, i) => (
        <figure
          key={`${img.url}-${i}`}
          className={styles.celda}
          // La destacada ocupa todas las filas de la columna izquierda.
          style={tipo === 'destacada' && i === 0 ? { gridRow: `span ${imagenes.length - 1}` } : undefined}
        >
          <img
            src={img.url}
            alt={img.etiqueta}
            width={ANCHO_REFERENCIA}
            height={ALTO_REFERENCIA}
            loading="lazy"
            decoding="async"
            style={estiloEncuadre(img)}
          />
          {img.etiqueta && <figcaption className={styles.etiqueta}>{img.etiqueta}</figcaption>}
        </figure>
      ))}
    </div>
  )
}