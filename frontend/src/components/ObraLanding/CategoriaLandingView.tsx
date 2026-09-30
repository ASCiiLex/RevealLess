import { useCallback, useEffect, useState } from 'react'
import styles from './CategoriaLandingView.module.css'
import Lomo from '../Carousel/Lomo'
import { fetchCategoriaLanding, type CategoriaLanding } from '../../api/categoriaLanding'

interface Props {
  categoriaId: number
}

export default function CategoriaLandingView({ categoriaId }: Props) {
  const [categoria, setCategoria] = useState<CategoriaLanding | null>(null)

  const cargar = useCallback(() => {
    fetchCategoriaLanding(categoriaId).then(setCategoria)
  }, [categoriaId])

  useEffect(() => {
    cargar()
  }, [cargar])

  if (!categoria) {
    return null
  }

  return (
    <div className={styles.wrapper}>
      <a className={styles.volver} href="/feed/">← Volver al feed</a>
      <h1 className={styles.titulo}>{categoria.nombre}</h1>
      <p className={styles.subtitulo}>
        {categoria.total_obras} obra{categoria.total_obras === 1 ? '' : 's'}
      </p>

      {categoria.obras.length === 0 ? (
        <p className={styles.vacio}>Todavía no hay obras en esta categoría.</p>
      ) : (
        <div className={styles.estante}>
          {categoria.obras.map((obra) => (
            <Lomo
              key={obra.id}
              obra={obra}
              activa={false}
              onSelect={(o) => {
                window.location.href = `/narrative/obra/${o.slug}/`
              }}
              mostrarProgreso
              onCambioSuscripcion={cargar}
            />
          ))}
        </div>
      )}
    </div>
  )
}