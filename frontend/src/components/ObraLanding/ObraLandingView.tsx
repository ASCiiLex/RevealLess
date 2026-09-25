import { useEffect, useState } from 'react'
import styles from './ObraLandingView.module.css'
import { fetchObraLanding, type ObraLanding } from '../../api/obraLanding'
import { crearSuscripcion, eliminarSuscripcion } from '../../api/suscripciones'
import { fetchProgreso, actualizarProgreso, type ProgresoData } from '../../api/progreso'
import { buildTree } from '../../utils/buildTree'
import UnidadNode from '../Progreso/UnidadNode'
import ConfirmModal from '../Progreso/ConfirmModal'

interface Props {
  obraSlug: string
}

export default function ObraLandingView({ obraSlug }: Props) {
  const [obra, setObra] = useState<ObraLanding | null>(null)
  const [progresoData, setProgresoData] = useState<ProgresoData | null>(null)
  const [sinopsisAbierta, setSinopsisAbierta] = useState(false)
  const [pendienteConfirmar, setPendienteConfirmar] = useState<{
    unidadId: number
    mensaje: string
  } | null>(null)

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

  async function handleSelectUnidad(unidadId: number, confirmado = false) {
    const resultado = await actualizarProgreso(obraSlug, unidadId, confirmado)

    if ('requiereConfirmacion' in resultado) {
      setPendienteConfirmar({ unidadId, mensaje: resultado.detail })
      return
    }

    setPendienteConfirmar(null)
    setProgresoData((prev) => (prev ? { ...prev, progreso: resultado } : prev))
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
          {obra.categorias.length > 0 && (
            <div className={styles.categorias}>
              {obra.categorias.map((c) => (
                <span key={c} className={styles.categoria}>{c}</span>
              ))}
            </div>
          )}
          <div className={styles.suscriptores}>
            {obra.total_suscriptores} suscriptor{obra.total_suscriptores === 1 ? '' : 'es'}
          </div>

          {obra.progreso_pct !== null && (
            <>
              <div className={styles.progresoTexto}>Tu progreso: {obra.progreso_pct}%</div>
              <div className={styles.progresoTrack}>
                <div className={styles.progresoFill} style={{ width: `${obra.progreso_pct}%` }} />
              </div>
            </>
          )}

          <div className={styles.actions}>
            <button
              className={`${styles.button} ${obra.suscrito ? '' : styles.buttonPrimary}`}
              onClick={handleToggleObra}
            >
              {obra.suscrito ? 'Siguiendo' : 'Seguir'}
            </button>
            <a className={styles.button} href={`/feed/react/?obra=${obra.id}`}>
              Ver feed
            </a>
            <a className={styles.button} href={`/narrative/obra/${obra.slug}/temas/`}>
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
          onConfirm={() => handleSelectUnidad(pendienteConfirmar.unidadId, true)}
          onCancel={() => setPendienteConfirmar(null)}
        />
      )}
    </div>
  )
}