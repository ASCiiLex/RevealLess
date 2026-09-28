import { useEffect, useState } from 'react'
import styles from './PasoProgreso.module.css'
import { fetchProgreso, actualizarProgreso, type UnidadNarrativa } from '../../api/progreso'
import UnidadNode from '../Progreso/UnidadNode'
import { buildTree } from '../../utils/buildTree'

interface Props {
  obraSlug: string
  obraTitulo: string
  onProgresoDeclarado: () => void
}

export default function PasoProgreso({ obraSlug, obraTitulo, onProgresoDeclarado }: Props) {
  const [unidades, setUnidades] = useState<UnidadNarrativa[] | null>(null)
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    fetchProgreso(obraSlug).then((data) => setUnidades(data.unidades))
  }, [obraSlug])

  async function handleSelect(unidadId: number) {
    setEnviando(true)
    try {
      const resultado = await actualizarProgreso(obraSlug, unidadId)
      // La primera declaración nunca exige confirmación de salto grande (mismo criterio que el backend).
      if (!('requiereConfirmacion' in resultado)) {
        onProgresoDeclarado()
      }
    } finally {
      setEnviando(false)
    }
  }

  if (!unidades) {
    return null
  }

  const arbol = buildTree(unidades)

  return (
    <div className={styles.wrapper}>
      <h2 className={styles.title}>¿Por dónde vas en {obraTitulo}?</h2>
      <p className={styles.subtitle}>Necesitamos saber tu progreso antes de publicar sobre esta obra.</p>

      <div className={styles.tree}>
        {arbol.map((nodo) => (
          <UnidadNode
            key={nodo.id}
            nodo={nodo}
            actualId={-1}
            actualOrden={-1}
            onSelect={enviando ? () => {} : handleSelect}
          />
        ))}
      </div>
    </div>
  )
}