import { useEffect, useState } from 'react'
import styles from './ProgresoView.module.css'
import UnidadNode from './UnidadNode'
import ConfirmModal from './ConfirmModal'
import { fetchProgreso, actualizarProgreso, type ProgresoData } from '../../api/progreso'
import { buildTree } from '../../utils/buildTree'

interface Props {
  obraSlug: string
}

export default function ProgresoView({ obraSlug }: Props) {
  const [data, setData] = useState<ProgresoData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pendienteConfirmar, setPendienteConfirmar] = useState<{
    unidadId: number
    mensaje: string
  } | null>(null)

  useEffect(() => {
    fetchProgreso(obraSlug)
      .then(setData)
      .catch(() => setError('No se pudo cargar el progreso de esta obra.'))
  }, [obraSlug])

  async function handleSelect(unidadId: number, confirmado = false) {
    setError(null)
    const resultado = await actualizarProgreso(obraSlug, unidadId, confirmado)

    if ('requiereConfirmacion' in resultado) {
      setPendienteConfirmar({ unidadId, mensaje: resultado.detail })
      return
    }

    setPendienteConfirmar(null)
    setData((prev) =>
      prev ? { ...prev, progreso: resultado } : prev
    )
  }

  if (error) {
    return (
      <div className={styles.wrapper}>
        <p className={styles.error}>{error}</p>
      </div>
    )
  }

  if (!data) {
    return null
  }

  const arbol = buildTree(data.unidades)
  const actualId = data.progreso?.unidad_actual.id ?? -1

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <a className={styles.backLink} href="/feed/react/">← Volver al feed</a>
        <h1 className={styles.title}>{data.obra.titulo}</h1>
        {data.progreso && (
          <p className={styles.currentProgress}>
            Progreso actual: {data.progreso.unidad_actual.etiqueta}
          </p>
        )}
      </div>

      {arbol.map((nodo) => (
        <UnidadNode
          key={nodo.id}
          nodo={nodo}
          actualId={actualId}
          onSelect={(id) => handleSelect(id)}
        />
      ))}

      {pendienteConfirmar && (
        <ConfirmModal
          mensaje={pendienteConfirmar.mensaje}
          onConfirm={() => handleSelect(pendienteConfirmar.unidadId, true)}
          onCancel={() => setPendienteConfirmar(null)}
        />
      )}
    </div>
  )
}