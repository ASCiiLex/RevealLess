import { useState } from 'react'
import PasoObra from './PasoObra'
import PasoProgreso from './PasoProgreso'
import PasoPost from './PasoPost'
import { existeProgreso } from '../../api/progreso'
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
    // Solo confirma si existe progreso, sin traer las unidades
    // completas (que en obras grandes son el coste real) -- si hace
    // falta declarar progreso, PasoProgreso las pide por su cuenta.
    const tieneProgreso = await existeProgreso(o.slug)
    setPaso(tieneProgreso ? 'post' : 'progreso')
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