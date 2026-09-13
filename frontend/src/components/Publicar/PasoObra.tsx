import { useEffect, useState } from 'react'
import styles from './PasoObra.module.css'
import { fetchCatalogoObras } from '../../api/obras'
import type { LomoObra } from '../Carousel/Lomo'

interface Props {
  onElegirObra: (obra: LomoObra) => void
}

export default function PasoObra({ onElegirObra }: Props) {
  const [obras, setObras] = useState<LomoObra[] | null>(null)
  const [slugSeleccionado, setSlugSeleccionado] = useState('')

  useEffect(() => {
    fetchCatalogoObras().then((data) => setObras([...data.biblioteca, ...data.descubrir]))
  }, [])

  function handleContinuar() {
    const obra = obras?.find((o) => o.slug === slugSeleccionado)
    if (obra) onElegirObra(obra)
  }

  if (!obras) {
    return null
  }

  return (
    <div className={styles.wrapper}>
      <h1 className={styles.title}>¿Sobre qué obra quieres publicar?</h1>

      <select
        className={styles.select}
        value={slugSeleccionado}
        onChange={(e) => setSlugSeleccionado(e.target.value)}
      >
        <option value="">Elige una obra</option>
        {obras.map((obra) => (
          <option key={obra.id} value={obra.slug}>{obra.titulo}</option>
        ))}
      </select>

      <button className={styles.button} onClick={handleContinuar} disabled={!slugSeleccionado}>
        Continuar
      </button>
    </div>
  )
}