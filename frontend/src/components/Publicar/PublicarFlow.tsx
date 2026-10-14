import { useRef, useState } from 'react'
import styles from './PublicarFlow.module.css'
import SelectorObra, { type ObraSeleccionada } from './SelectorObra'
import PasoProgreso from './PasoProgreso'
import PasoPost from './PasoPost'
import Comparativa, { COMPARATIVA_VACIA, InterruptorComparativa, type EstadoComparativa } from './Comparativa'
import { existeProgreso } from '../../api/progreso'
import type { TemaPublicable } from '../../api/publicar'

type Estado = 'sin-obra' | 'cargando' | 'progreso' | 'post'

// Orden: obra → ¿comparativo? → segunda obra → resto del formulario.
export default function PublicarFlow() {
  const [obra, setObra] = useState<ObraSeleccionada | null>(null)
  const [temaId, setTemaId] = useState<number | null>(null)
  const [estado, setEstado] = useState<Estado>('sin-obra')
  const [comparativa, setComparativa] = useState<EstadoComparativa>(COMPARATIVA_VACIA)
  const obraActual = useRef<string | null>(null)

  async function seleccionar(o: ObraSeleccionada, tema: number | null) {
    obraActual.current = o.slug
    setObra(o)
    setTemaId(tema)
    setEstado('cargando')
    // Solo el booleano: el árbol completo lo pide PasoProgreso si hace falta.
    const tieneProgreso = await existeProgreso(o.slug)
    // Descarta la respuesta si el usuario cambió de obra mientras tanto.
    if (obraActual.current === o.slug) {
      setEstado(tieneProgreso ? 'post' : 'progreso')
    }
  }

  function handleElegirTema(tema: TemaPublicable) {
    seleccionar({ slug: tema.obra_slug, titulo: tema.obra_titulo }, tema.id)
  }

  function handleCambiar() {
    obraActual.current = null
    setObra(null)
    setTemaId(null)
    setEstado('sin-obra')
  }

  return (
    <div className={styles.wrapper}>
      <h1 className={styles.title}>Publicar</h1>

      <SelectorObra
        seleccion={obra}
        onElegirObra={(o) => seleccionar(o, null)}
        onElegirTema={handleElegirTema}
        onCambiar={handleCambiar}
      />

      <InterruptorComparativa valor={comparativa} onChange={setComparativa} />

      {comparativa.activa && (
        <Comparativa obraPrincipalSlug={obra?.slug ?? null} valor={comparativa} onChange={setComparativa} />
      )}

      {estado === 'progreso' && obra ? (
        <PasoProgreso
          key={obra.slug}
          obraSlug={obra.slug}
          obraTitulo={obra.titulo}
          onProgresoDeclarado={() => setEstado('post')}
        />
      ) : (
        <PasoPost
          key={`${obra?.slug ?? 'sin-obra'}-${temaId ?? ''}`}
          obraSlug={estado === 'post' && obra ? obra.slug : null}
          temaIdInicial={temaId}
          comparativa={comparativa}
          onPublicado={() => {
            window.location.href = '/feed/'
          }}
          onProgresoRequerido={() => setEstado('progreso')}
        />
      )}
    </div>
  )
}