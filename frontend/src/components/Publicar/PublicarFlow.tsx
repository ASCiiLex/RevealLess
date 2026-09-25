import { useState } from 'react'
import PasoObra from './PasoObra'
import PasoProgreso from './PasoProgreso'
import PasoPost from './PasoPost'
import { fetchProgreso } from '../../api/progreso'
import type { TemaBusqueda } from '../../api/buscar'

type Paso = 'obra' | 'cargando' | 'progreso' | 'post'

interface ObraSeleccionada {
  slug: string
  titulo: string
}

export default function PublicarFlow() {
  const [paso, setPaso] = useState<Paso>('obra')
  const [obra, setObra] = useState<ObraSeleccionada | null>(null)
  const [temaId, setTemaId] = useState<number | null>(null)

  async function irAPaso(o: ObraSeleccionada) {
    setObra(o)
    setPaso('cargando')
    // Fuente de verdad real (no heurística sobre datos del catálogo):
    // se consulta si existe progreso antes de decidir el paso, para no
    // llegar al formulario y descubrir el 409 a mitad de escritura.
    const data = await fetchProgreso(o.slug)
    setPaso(data.progreso ? 'post' : 'progreso')
  }

  function handleElegirObra(o: ObraSeleccionada) {
    setTemaId(null)
    irAPaso(o)
  }

  function handleElegirTema(tema: TemaBusqueda) {
    setTemaId(tema.id)
    irAPaso({ slug: tema.obra_slug, titulo: tema.obra_titulo })
  }

  if (paso === 'obra') {
    return <PasoObra onElegirObra={handleElegirObra} onElegirTema={handleElegirTema} />
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
        temaIdInicial={temaId}
        onPublicado={() => {
          window.location.href = '/feed/react/'
        }}
        onProgresoRequerido={() => setPaso('progreso')}
      />
    )
  }

  return null
}