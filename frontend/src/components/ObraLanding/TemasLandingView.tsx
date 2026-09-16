import { useEffect, useState } from 'react'
import styles from './TemasLandingView.module.css'
import { fetchObraLanding, type ObraLanding, type TemaLanding } from '../../api/obraLanding'
import { crearSuscripcion, eliminarSuscripcion } from '../../api/suscripciones'

interface Props {
  obraSlug: string
}

export default function TemasLandingView({ obraSlug }: Props) {
  const [obra, setObra] = useState<ObraLanding | null>(null)

  useEffect(() => {
    fetchObraLanding(obraSlug).then(setObra)
  }, [obraSlug])

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
        <a className={styles.backLink} href={`/narrative/obra/${obra.slug}/react/`}>← Volver a {obra.titulo}</a>
        <h1 className={styles.title}>Temas</h1>
      </div>

      {obra.temas.length === 0 ? (
        <p className={styles.empty}>Esta obra aún no tiene temas registrados.</p>
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