import { useState } from 'react'
import styles from './SearchResults.module.css'
import type { ResultadoBusqueda, TemaBusqueda } from '../../api/buscar'
import { crearSuscripcion } from '../../api/suscripciones'
import type { LomoObra } from '../Carousel/Lomo'

interface Props {
  resultado: ResultadoBusqueda
}

export default function SearchResults({ resultado }: Props) {
  const sinResultados = resultado.obras.length === 0 && resultado.temas.length === 0

  if (sinResultados) {
    return (
      <div className={styles.dropdown}>
        <p className={styles.empty}>Sin resultados.</p>
      </div>
    )
  }

  return (
    <div className={styles.dropdown}>
      {resultado.obras.length > 0 && (
        <>
          <div className={styles.groupLabel}>Obras</div>
          {resultado.obras.map((obra) => (
            <ObraRow key={obra.id} obra={obra} />
          ))}
        </>
      )}

      {resultado.temas.length > 0 && (
        <>
          <div className={styles.groupLabel}>Temas</div>
          {resultado.temas.map((tema) => (
            <TemaRow key={tema.id} tema={tema} />
          ))}
        </>
      )}
    </div>
  )
}

function ObraRow({ obra }: { obra: LomoObra }) {
  const [siguiendo, setSiguiendo] = useState(obra.suscrito)
  const [cargando, setCargando] = useState(false)

  async function handleSeguir() {
    if (siguiendo || cargando) return
    setCargando(true)
    try {
      await crearSuscripcion(obra.slug)
      setSiguiendo(true)
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className={styles.row}>
      <div className={styles.rowMain}>
        <img className={styles.thumb} src={obra.imagen_url} alt="" />
        <span className={styles.titulo}>{obra.titulo}</span>
      </div>
      <button
        className={`${styles.followButton} ${siguiendo ? styles.followButtonActive : ''}`}
        onClick={handleSeguir}
        disabled={siguiendo || cargando}
      >
        {siguiendo ? 'Siguiendo' : 'Seguir'}
      </button>
    </div>
  )
}

function TemaRow({ tema }: { tema: TemaBusqueda }) {
  const [siguiendo, setSiguiendo] = useState(false)
  const [cargando, setCargando] = useState(false)

  async function handleSeguir() {
    if (siguiendo || cargando) return
    setCargando(true)
    try {
      await crearSuscripcion(tema.obra_slug, { temaId: tema.id })
      setSiguiendo(true)
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className={styles.row}>
      <div className={styles.rowMain}>
        <div>
          <div className={styles.titulo}>{tema.nombre}</div>
          <div className={styles.subtitulo}>{tema.obra_titulo}</div>
        </div>
      </div>
      <button
        className={`${styles.followButton} ${siguiendo ? styles.followButtonActive : ''}`}
        onClick={handleSeguir}
        disabled={siguiendo || cargando}
      >
        {siguiendo ? 'Siguiendo' : 'Seguir'}
      </button>
    </div>
  )
}