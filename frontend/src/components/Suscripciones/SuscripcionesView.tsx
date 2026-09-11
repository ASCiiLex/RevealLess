import { useEffect, useState } from 'react'
import styles from './SuscripcionesView.module.css'
import SuscripcionRow from './SuscripcionRow'
import AddSuscripcionForm from './AddSuscripcionForm'
import { fetchSuscripciones, eliminarSuscripcion, type Suscripcion } from '../../api/suscripciones'
import { fetchCatalogoObras } from '../../api/obras'
import type { LomoObra } from '../Carousel/Lomo'

export default function SuscripcionesView() {
  const [suscripciones, setSuscripciones] = useState<Suscripcion[] | null>(null)
  const [catalogo, setCatalogo] = useState<LomoObra[]>([])
  const [formAbierto, setFormAbierto] = useState(false)

  useEffect(() => {
    fetchSuscripciones()
      .then(setSuscripciones)
      .catch(() => setSuscripciones([]))

    fetchCatalogoObras()
      .then((data) => setCatalogo([...data.biblioteca, ...data.descubrir]))
      .catch(() => setCatalogo([]))
  }, [])

  async function handleRemove(id: number) {
    await eliminarSuscripcion(id)
    setSuscripciones((prev) => prev?.filter((s) => s.id !== id) ?? null)
  }

  function handleCreated(nueva: Suscripcion) {
    setSuscripciones((prev) => (prev ? [nueva, ...prev] : [nueva]))
    setFormAbierto(false)
  }

  if (!suscripciones) {
    return null
  }

  return (
    <div className={styles.wrapper}>
      <h1 className={styles.title}>Suscripciones</h1>
      <p className={styles.subtitle}>Obras, arcos y temas que sigues</p>

      {formAbierto ? (
        <AddSuscripcionForm
          obras={catalogo}
          onCreated={handleCreated}
          onCancel={() => setFormAbierto(false)}
        />
      ) : (
        <button className={styles.addButton} onClick={() => setFormAbierto(true)}>
          <span aria-hidden="true">＋</span>
          <span>Añadir suscripción</span>
        </button>
      )}

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