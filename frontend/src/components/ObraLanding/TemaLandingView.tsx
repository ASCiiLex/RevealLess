import { useEffect, useState } from 'react'
import styles from './TemaLandingView.module.css'
import { fetchTemaLanding, type TemaLanding } from '../../api/temaLanding'
import { crearSuscripcion, eliminarSuscripcion } from '../../api/suscripciones'

interface Props {
  temaId: number
}

export default function TemaLandingView({ temaId }: Props) {
  const [tema, setTema] = useState<TemaLanding | null>(null)
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    fetchTemaLanding(temaId).then(setTema)
  }, [temaId])

  async function handleToggleSeguir() {
    if (!tema || cargando) return
    setCargando(true)
    try {
      if (tema.suscrito) {
        if (tema.suscripcion_id !== null) {
          await eliminarSuscripcion(tema.suscripcion_id)
        }
        setTema({ ...tema, suscrito: false, suscripcion_id: null })
      } else {
        const suscripcion = await crearSuscripcion(tema.obra_slug, { temaId: tema.id })
        setTema({ ...tema, suscrito: true, suscripcion_id: suscripcion.id })
      }
    } finally {
      setCargando(false)
    }
  }

  if (!tema) {
    return null
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <h1 className={styles.title}>{tema.nombre}</h1>
        <div className={styles.suscriptores}>
          {tema.total_suscriptores} suscriptor{tema.total_suscriptores === 1 ? '' : 'es'}
        </div>

        {tema.obras.length > 1 && (
          <div className={styles.obrasChips}>
            {tema.obras.map((o) => (
              <a key={o.id} className={styles.obraChip} href={`/narrative/obra/${o.slug}/`}>
                {o.titulo}
              </a>
            ))}
          </div>
        )}
      </div>

      <div className={styles.actions}>
        <button
          className={`${styles.button} ${tema.suscrito ? '' : styles.buttonPrimary}`}
          onClick={handleToggleSeguir}
          disabled={cargando}
        >
          {tema.suscrito ? 'Siguiendo' : 'Seguir'}
        </button>
        <a className={styles.button} href={`/feed/react/?tema=${tema.id}`}>
          Ver feed
        </a>
      </div>
    </div>
  )
}