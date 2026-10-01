import { useEffect, useState } from 'react'
import styles from './ObraLandingView.module.css'
import botones from '../../styles/botones.module.css'
import { fetchObraLanding, type ObraLanding } from '../../api/obraLanding'
import { crearSuscripcion, crearSuscripcionPersonaje, eliminarSuscripcion } from '../../api/suscripciones'
import { fetchProgreso, actualizarProgreso, type ProgresoData } from '../../api/progreso'
import { buildTree } from '../../utils/buildTree'
import { calcularProgresoPct } from '../../utils/progresoPct'
import UnidadNode from '../Progreso/UnidadNode'
import ConfirmModal from '../Progreso/ConfirmModal'
import ProgresoSlider from './ProgresoSlider'

interface Props {
  obraSlug: string
}

interface Pendiente {
  unidadId: number
  mensaje: string
  retroceso: boolean
}

export default function ObraLandingView({ obraSlug }: Props) {
  const [obra, setObra] = useState<ObraLanding | null>(null)
  const [progresoData, setProgresoData] = useState<ProgresoData | null>(null)
  const [sinopsisAbierta, setSinopsisAbierta] = useState(false)
  const [pendienteConfirmar, setPendienteConfirmar] = useState<Pendiente | null>(null)
  // Remonta el deslizador al resolver (aplicado o cancelado) para volver al progreso real.
  const [sliderKey, setSliderKey] = useState(0)

  useEffect(() => {
    fetchObraLanding(obraSlug).then(setObra)
    fetchProgreso(obraSlug).then(setProgresoData)
  }, [obraSlug])

  async function handleToggleObra() {
    if (!obra) return
    if (obra.suscrito) {
      if (obra.suscripcion_id !== null) {
        await eliminarSuscripcion(obra.suscripcion_id)
      }
      setObra({ ...obra, suscrito: false, suscripcion_id: null })
    } else {
      const suscripcion = await crearSuscripcion(obra.slug)
      setObra({ ...obra, suscrito: true, suscripcion_id: suscripcion.id })
    }
  }

  async function handleTogglePersonaje(personajeId: number, suscripcionId: number | null) {
    let nuevoId: number | null = null
    if (suscripcionId !== null) {
      await eliminarSuscripcion(suscripcionId)
    } else {
      nuevoId = (await crearSuscripcionPersonaje(personajeId)).id
    }
    setObra((prev) =>
      prev
        ? {
            ...prev,
            personajes: prev.personajes.map((p) =>
              p.id === personajeId ? { ...p, suscripcion_id: nuevoId } : p
            ),
          }
        : prev
    )
  }

  async function handleSelectUnidad(unidadId: number, confirmado = false) {
    const resultado = await actualizarProgreso(obraSlug, unidadId, confirmado)

    if ('requiereConfirmacion' in resultado) {
      setPendienteConfirmar({ unidadId, mensaje: resultado.detail, retroceso: resultado.salto < 0 })
      return
    }

    setPendienteConfirmar(null)
    setProgresoData((prev) => (prev ? { ...prev, progreso: resultado } : prev))
    setSliderKey((k) => k + 1)

    // Barra al instante; después se refresca la landing para los personajes ya desbloqueados.
    if (progresoData) {
      const longitudTotal = Math.max(0, ...progresoData.unidades.map((u) => u.orden_fin))
      const pct = calcularProgresoPct(resultado.orden_absoluto, longitudTotal)
      setObra((prev) => (prev ? { ...prev, progreso_pct: pct } : prev))
    }
    fetchObraLanding(obraSlug).then(setObra)
  }

  function cancelarConfirmacion() {
    setPendienteConfirmar(null)
    setSliderKey((k) => k + 1)
  }

  if (!obra) {
    return null
  }

  const arbol = progresoData ? buildTree(progresoData.unidades) : []
  const actualId = progresoData?.progreso?.unidad_actual.id ?? -1
  const actualOrden = progresoData?.progreso?.unidad_actual.orden_inicio ?? -1

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <img className={styles.imagen} src={obra.imagen_url} alt="" />
        <div className={styles.info}>
          <h1 className={styles.titulo}>{obra.titulo}</h1>
          {obra.categorias_detalle.length > 0 && (
            <div className={styles.categorias}>
              {obra.categorias_detalle.map((c) => (
                <a key={c.id} className={styles.categoria} href={`/narrative/categoria/${c.id}/`}>
                  {c.nombre}
                </a>
              ))}
            </div>
          )}
          <div className={styles.suscriptores}>
            {obra.total_suscriptores} suscriptor{obra.total_suscriptores === 1 ? '' : 'es'}
          </div>

          {progresoData && (
            <ProgresoSlider
              key={sliderKey}
              unidades={progresoData.unidades}
              ordenActual={progresoData.progreso?.orden_absoluto ?? null}
              pct={obra.progreso_pct}
              onCommit={(id) => handleSelectUnidad(id)}
            />
          )}

          <div className={styles.actions}>
            {obra.suscrito ? (
              <button
                className={botones.activo}
                onClick={handleToggleObra}
                aria-label={`Dejar de seguir ${obra.titulo}`}
              >
                <span className={botones.enReposo}>✓ Siguiendo</span>
                <span className={botones.alPasar}>Dejar de seguir</span>
              </button>
            ) : (
              <button className={botones.primario} onClick={handleToggleObra}>
                Seguir
              </button>
            )}
            <a className={botones.secundario} href={`/feed/?obra=${obra.id}`}>
              Ver feed
            </a>
            <a className={botones.secundario} href={`/narrative/obra/${obra.slug}/temas/`}>
              Temas
            </a>
          </div>
        </div>
      </div>

      {obra.sinopsis && (
        <div className={styles.sinopsisBox}>
          <button
            className={styles.sinopsisToggle}
            onClick={() => setSinopsisAbierta((v) => !v)}
            aria-expanded={sinopsisAbierta}
          >
            <span>Sinopsis</span>
            <span className={styles.chevron} aria-hidden="true">{sinopsisAbierta ? '▾' : '▸'}</span>
          </button>
          {sinopsisAbierta && <p className={styles.sinopsisText}>{obra.sinopsis}</p>}
        </div>
      )}

      {obra.obras_relacionadas.length > 0 && (
        <section className={styles.bloque}>
          <h2 className={styles.bloqueTitulo}>Obras relacionadas</h2>
          <div className={styles.relacionadas}>
            {obra.obras_relacionadas.map((o) => (
              <a key={o.id} className={styles.relacionada} href={`/narrative/obra/${o.slug}/`}>
                {o.titulo}
              </a>
            ))}
          </div>
        </section>
      )}

      <section className={styles.bloque}>
        <h2 className={styles.bloqueTitulo}>Personajes</h2>
        {obra.personajes.length > 0 ? (
          <div className={styles.personajes}>
            {obra.personajes.map((p) => {
              const siguiendo = p.suscripcion_id !== null
              return (
                <div key={p.id} className={styles.personaje}>
                  <a className={styles.personajeEnlace} href={`/narrative/personaje/${p.id}/`}>
                    <img className={styles.personajeImagen} src={p.imagen_url} alt="" />
                    <span className={styles.personajeNombre}>{p.nombre}</span>
                    {p.nota && <span className={styles.personajeNota}>{p.nota}</span>}
                  </a>
                  <button
                    className={`${styles.personajeSeguir} ${siguiendo ? styles.personajeSiguiendo : ''}`}
                    onClick={() => handleTogglePersonaje(p.id, p.suscripcion_id)}
                    aria-pressed={siguiendo}
                    aria-label={siguiendo ? `Dejar de seguir a ${p.nombre}` : `Seguir a ${p.nombre}`}
                  >
                    {siguiendo ? '✓ Siguiendo' : '+ Seguir'}
                  </button>
                </div>
              )
            })}
          </div>
        ) : (
          <p className={styles.bloqueVacio}>
            {obra.progreso_pct === null
              ? 'Declara tu progreso para ver los personajes que ya conoces.'
              : 'Aún no has llegado a la aparición de ningún personaje registrado.'}
          </p>
        )}
      </section>

      <h2 className={styles.progresoTitle}>Progreso</h2>
      {progresoData?.progreso && (
        <p className={styles.currentProgress}>
          Progreso actual: {progresoData.progreso.unidad_actual.etiqueta}
        </p>
      )}
      {progresoData && (
        <div className={styles.tree}>
          {arbol.map((nodo) => (
            <UnidadNode
              key={nodo.id}
              nodo={nodo}
              actualId={actualId}
              actualOrden={actualOrden}
              onSelect={(id) => handleSelectUnidad(id)}
              autoScroll={false}
            />
          ))}
        </div>
      )}

      {pendienteConfirmar && (
        <ConfirmModal
          mensaje={pendienteConfirmar.mensaje}
          textoConfirmar={pendienteConfirmar.retroceso ? 'Retroceder' : 'Confirmar salto'}
          onConfirm={() => handleSelectUnidad(pendienteConfirmar.unidadId, true)}
          onCancel={cancelarConfirmacion}
        />
      )}
    </div>
  )
}