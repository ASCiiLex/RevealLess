import { useEffect, useState } from 'react'
import styles from './PasoObra.module.css'
import { fetchProgreso } from '../../api/progreso'
import { actualizarProgreso } from '../../api/progreso'
import UnidadNode from '../Progreso/UnidadNode'
import { buildTree } from '../../utils/buildTree'

interface Props {
  obraSlug: string
  obraTitulo: string
  onProgresoDeclarado: () => void
}

export default function PasoProgreso({ obraSlug, obraTitulo, onProgresoDeclarado }: Props) {
  const [unidades, setUnidades] = useState<Awaited<ReturnType<typeof fetchProgreso>>['unidades'] | null>(null)

  useEffect(() => {
    fetchProgreso(obraSlug).then((data) => setUnidades(data.unidades))
  }, [obraSlug])

  async function handleSelect(unidadId: number) {
    const resultado = await actualizarProgreso(obraSlug, unidadId)
    if (!('requiereConfirmacion' in resultado)) {
      onProgresoDeclarado()
    }
    // La primera declaración de progreso nunca exige confirmación de
    // salto grande (mismo criterio que actualizar_progreso() en
    // backend), así que este caso límite no debería darse aquí en la
    // práctica -- se deja sin manejar explícitamente por eso.
  }

  if (!unidades) {
    return null
  }

  const arbol = buildTree(unidades)

  return (
    <div className={styles.wrapper}>
      <h1 className={styles.title}>¿Por dónde vas en {obraTitulo}?</h1>
      <p>Necesitamos saber tu progreso antes de publicar sobre esta obra.</p>

      {arbol.map((nodo) => (
        <UnidadNode key={nodo.id} nodo={nodo} actualId={-1} onSelect={handleSelect} />
      ))}
    </div>
  )
}