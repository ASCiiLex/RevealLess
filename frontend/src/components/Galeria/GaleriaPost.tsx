import { useState } from 'react'
import styles from './GaleriaPost.module.css'

export interface ImagenGaleria {
  url: string
  etiqueta: string
}

interface Props {
  imagenes: ImagenGaleria[]
  disposicion?: string | null
}

export const MAX_IMAGENES = 4

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

function Deslizador({ antes, despues }: { antes: ImagenGaleria; despues: ImagenGaleria }) {
  const [posicion, setPosicion] = useState(50)
  return (
    <div className={styles.deslizador}>
      <img className={styles.capa} src={despues.url} alt={despues.etiqueta} />
      <img
        className={styles.capa}
        src={antes.url}
        alt={antes.etiqueta}
        style={{ clipPath: `inset(0 ${100 - posicion}% 0 0)` }}
      />
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
    return <img className={styles.unica} src={imagenes[0].url} alt={imagenes[0].etiqueta} />
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
          <img src={img.url} alt={img.etiqueta} loading="lazy" />
          {img.etiqueta && <figcaption className={styles.etiqueta}>{img.etiqueta}</figcaption>}
        </figure>
      ))}
    </div>
  )
}