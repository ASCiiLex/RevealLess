import { useEffect, useState } from 'react'
import styles from './SuscripcionesView.module.css'
import SuscripcionRow from './SuscripcionRow'
import { fetchSuscripciones, eliminarSuscripcion, type Suscripcion } from '../../api/suscripciones'

export default function SuscripcionesView() {
  const [suscripciones, setSuscripciones] = useState<Suscripcion[] | null>(null)

  useEffect(() => {
    fetchSuscripciones()
      .then(setSuscripciones)
      .catch(() => setSuscripciones([]))
  }, [])

  async function handleRemove(id: number) {
    await eliminarSuscripcion(id)
    setSuscripciones((prev) => prev?.filter((s) => s.id !== id) ?? null)
  }

  if (!suscripciones) {
    return null
  }

  return (
    <div className={styles.wrapper}>
      <h1 className={styles.title}>Suscripciones</h1>
      <p className={styles.subtitle}>Obras, arcos y temas que sigues</p>

      {suscripciones.length === 0 ? (
        <p className={styles.empty}>
          Todavía no sigues nada. Ve a Descubrir para encontrar obras que seguir.
        </p>
      ) : (
        suscripciones.map((s) => (
          <SuscripcionRow key={s.id} suscripcion={s} onRemove={handleRemove} />
        ))
      )}
    </div>
  )
}