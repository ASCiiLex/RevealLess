cat > frontend/src/components/ObraLanding/PersonajeLandingView.tsx << 'EOF'
import { useEffect, useState } from 'react'
import styles from './PersonajeLandingView.module.css'
import botones from '../../styles/botones.module.css'
import { fetchPersonajeLanding, type PersonajeDetalle } from '../../api/personajeLanding'
import { crearSuscripcionPersonaje, eliminarSuscripcion } from '../../api/suscripciones'

interface Props {
  personajeId: number
}

export default function PersonajeLandingView({ personajeId }: Props) {
  const [personaje, setPersonaje] = useState<PersonajeDetalle | null>(null)
  const [noDisponible, setNoDisponible] = useState(false)
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    fetchPersonajeLanding(personajeId)
      .then(setPersonaje)
      .catch(() => setNoDisponible(true))
  }, [personajeId])

  async function handleToggleSeguir() {
    if (!personaje || cargando) return
    setCargando(true)
    try {
      if (personaje.suscripcion_id !== null) {
        await eliminarSuscripcion(personaje.suscripcion_id)
        setPersonaje({
          ...personaje,
          suscripcion_id: null,
          total_suscriptores: Math.max(0, personaje.total_suscriptores - 1),
        })
      } else {
        const suscripcion = await crearSuscripcionPersonaje(personaje.id)
        setPersonaje({
          ...personaje,
          suscripcion_id: suscripcion.id,
          total_suscriptores: personaje.total_suscriptores + 1,
        })
      }
    } finally {
      setCargando(false)
    }
  }

  if (noDisponible) {
    return (
      <div className={styles.wrapper}>
        <p className={styles.aviso}>
          Este personaje no está disponible. <a href="/feed/">Volver al feed</a>
        </p>
      </div>
    )
  }

  if (!personaje) {
    return null
  }

  const siguiendo = personaje.suscripcion_id !== null

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <img className={styles.imagen} src={personaje.imagen_url} alt="" />
        <div className={styles.info}>
          <h1 className={styles.titulo}>{personaje.nombre}</h1>
          <div className={styles.suscriptores}>
            {personaje.total_suscriptores} suscriptor{personaje.total_suscriptores === 1 ? '' : 'es'}
          </div>
          <div className={styles.actions}>
            {siguiendo ? (
              <button
                className={botones.activo}
                onClick={handleToggleSeguir}
                disabled={cargando}
                aria-label={`Dejar de seguir a ${personaje.nombre}`}
              >
                <span className={botones.enReposo}>✓ Siguiendo</span>
                <span className={botones.alPasar}>Dejar de seguir</span>
              </button>
            ) : (
              <button className={botones.primario} onClick={handleToggleSeguir} disabled={cargando}>
                Seguir
              </button>
            )}
            <a className={botones.secundario} href={`/feed/?personaje=${personaje.id}`}>
              Ver feed
            </a>
          </div>
        </div>
      </div>

      <section className={styles.bloque}>
        <h2 className={styles.bloqueTitulo}>Aparece en</h2>
        <div className={styles.obras}>
          {personaje.obras.map((o) => (
            <a key={o.id} className={styles.obra} href={`/narrative/obra/${o.slug}/`}>
              <img className={styles.obraImagen} src={o.imagen_url} alt="" />
              <span className={styles.obraTitulo}>{o.titulo}</span>
            </a>
          ))}
        </div>
        <p className={styles.nota}>Solo se muestran las obras en las que ya has llegado a su aparición.</p>
      </section>
    </div>
  )
}
EOF