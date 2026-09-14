import { useEffect, useState } from 'react'
import styles from './ObraLandingView.module.css'
import { fetchObraLanding, type ObraLanding, type TemaLanding } from '../../api/obraLanding'
import { crearSuscripcion, eliminarSuscripcion } from '../../api/suscripciones'

interface Props {
  obraSlug: string
}

export default function ObraLandingView({ obraSlug }: Props) {
  const [obra, setObra] = useState<ObraLanding | null>(null)

  useEffect(() => {
    fetchObraLanding(obraSlug).then(setObra)
  }, [obraSlug])

  async function handleToggleObra() {
    if (!obra) return
    if (obra.suscrito) {
      if (obra.suscripcion_id !== null) {
        await eliminarSuscripcion(obra.suscripcion_id)
      }
      setObra({ ...obra, suscrito: false, suscripcion_id: null })
    } else {
      const suscripcion = await crearSuscripcion(obra.slug)
      setObra({ ...obra, suscrito: true, suscripcion_id: suscripcion.id })
    }
  }

  async function handleToggleTema(tema: TemaLanding) {
    if (!obra) return
    if (tema.suscrito) {
      if (tema.suscripcion_id !== null) {
        await eliminarSuscripcion(tema.suscripcion_id)
      }
      setObra({
        ...obra,
        temas: obra.temas.map((t) =>
          t.id === tema.id ? { ...t, suscrito: false, suscripcion_id: null } : t
        ),
      })
    } else {
      const suscripcion = await crearSuscripcion(obra.slug, { temaId: tema.id })
      setObra({
        ...obra,
        temas: obra.temas.map((t) =>
          t.id === tema.id ? { ...t, suscrito: true, suscripcion_id: suscripcion.id } : t
        ),
      })
    }
  }

  if (!obra) {
    return null
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <img className={styles.imagen} src={obra.imagen_url} alt="" />
        <div className={styles.info}>
          <h1 className={styles.titulo}>{obra.titulo}</h1>
          {obra.categorias.length > 0 && (
            <div className={styles.categorias}>
              {obra.categorias.map((c) => (
                <span key={c} className={styles.categoria}>{c}</span>
              ))}
            </div>
          )}
          <div className={styles.suscriptores}>
            {obra.total_suscriptores} suscriptor{obra.total_suscriptores === 1 ? '' : 'es'}
          </div>
        </div>
      </div>

      {obra.sinopsis && <p className={styles.sinopsis}>{obra.sinopsis}</p>}

      {obra.progreso_pct !== null && (
        <p className={styles.progreso}>Tu progreso: {obra.progreso_pct}%</p>
      )}

      <div className={styles.actions}>
        <button
          className={`${styles.button} ${obra.suscrito ? '' : styles.buttonPrimary}`}
          onClick={handleToggleObra}
        >
          {obra.suscrito ? 'Siguiendo' : 'Seguir'}
        </button>
        <a className={styles.button} href={`/feed/react/?obra=${obra.id}`}>
          Ver feed
        </a>
        <a className={styles.button} href={`/narrative/progreso-react/${obra.slug}/`}>
          Progreso
        </a>
      </div>

      <h2 className={styles.temasTitle}>Temas</h2>
      {obra.temas.length === 0 ? (
        <p className={styles.emptyTemas}>Esta obra aún no tiene temas registrados.</p>
      ) : (
        obra.temas.map((tema) => (
          <div key={tema.id} className={styles.temaRow}>
            <span className={styles.temaNombre}>{tema.nombre}</span>
            <button
              className={`${styles.temaButton} ${tema.suscrito ? styles.temaButtonActive : ''}`}
              onClick={() => handleToggleTema(tema)}
            >
              {tema.suscrito ? 'Siguiendo' : 'Seguir'}
            </button>
          </div>
        ))
      )}
    </div>
  )
}