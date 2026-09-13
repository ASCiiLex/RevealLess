import { useState } from 'react'
import PasoObra from './PasoObra'
import PasoProgreso from './PasoProgreso'
import PasoPost from './PasoPost'
import { fetchProgreso } from '../../api/progreso'
import type { LomoObra } from '../Carousel/Lomo'

type Paso = 'obra' | 'cargando' | 'progreso' | 'post'

export default function PublicarFlow() {
  const [paso, setPaso] = useState<Paso>('obra')
  const [obra, setObra] = useState<LomoObra | null>(null)

  async function handleElegirObra(o: LomoObra) {
    setObra(o)
    setPaso('cargando')
    // Fuente de verdad real (no heurística sobre datos del catálogo):
    // se consulta si existe progreso antes de decidir el paso, para no
    // llegar al formulario y descubrir el 409 a mitad de escritura.
    const data = await fetchProgreso(o.slug)
    setPaso(data.progreso ? 'post' : 'progreso')
  }

  if (paso === 'obra') {
    return <PasoObra onElegirObra={handleElegirObra} />
  }

  if (paso === 'cargando') {
    return null
  }

  if (paso === 'progreso' && obra) {
    return (
      <PasoProgreso
        obraSlug={obra.slug}
        obraTitulo={obra.titulo}
        onProgresoDeclarado={() => setPaso('post')}
      />
    )
  }

  if (paso === 'post' && obra) {
    return (
      <PasoPost
        obraSlug={obra.slug}
        obraTitulo={obra.titulo}
        onPublicado={() => {
          window.location.href = '/feed/react/'
        }}
        onProgresoRequerido={() => setPaso('progreso')}
      />
    )
  }

  return null
}