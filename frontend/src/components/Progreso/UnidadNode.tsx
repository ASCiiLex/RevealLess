import { useEffect, useRef, useState } from 'react'
import styles from './UnidadNode.module.css'
import { contieneActual, type TreeNode } from '../../utils/buildTree'

const UMBRAL_SCROLL = 8 // más de esto usa contenedor con scroll interno

interface Props {
  nodo: TreeNode
  actualId: number
  onSelect: (unidadId: number) => void
}

export default function UnidadNode({ nodo, actualId, onSelect }: Props) {
  const tieneActual = contieneActual(nodo, actualId)
  const [abierto, setAbierto] = useState(tieneActual)
  const esHoja = nodo.hijos.length === 0

  if (esHoja) {
    const esActual = nodo.id === actualId
    return (
      <button
        className={`${styles.leaf} ${esActual ? styles.leafActual : ''}`}
        onClick={() => onSelect(nodo.id)}
      >
        <span>{nodo.etiqueta}{esActual ? ' · actual' : ''}</span>
      </button>
    )
  }

  const usarScroll = nodo.hijos.length > UMBRAL_SCROLL && nodo.hijos.every((h) => h.hijos.length === 0)

  return (
    <div className={styles.node}>
      <button
        className={`${styles.header} ${tieneActual ? styles.headerActual : ''}`}
        onClick={() => setAbierto((v) => !v)}
        aria-expanded={abierto}
      >
        <span className={styles.nombre}>{nodo.etiqueta}</span>
        <span className={styles.chevron} aria-hidden="true">{abierto ? '▾' : '▸'}</span>
      </button>

      {abierto && (
        <div className={styles.children}>
          {usarScroll ? (
            <ScrollAcotado hijos={nodo.hijos} actualId={actualId} onSelect={onSelect} />
          ) : (
            nodo.hijos.map((hijo) => (
              <UnidadNode key={hijo.id} nodo={hijo} actualId={actualId} onSelect={onSelect} />
            ))
          )}
        </div>
      )}
    </div>
  )
}

function ScrollAcotado({
  hijos,
  actualId,
  onSelect,
}: {
  hijos: TreeNode[]
  actualId: number
  onSelect: (id: number) => void
}) {
  const actualRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    actualRef.current?.scrollIntoView({ block: 'center' })
  }, [])

  const ordenActual = hijos.find((h) => h.id === actualId)?.orden_inicio ?? 0

  return (
    <div className={styles.scrollBox}>
      {hijos.map((hijo) => {
        const esActual = hijo.id === actualId
        const esPasado = hijo.orden_inicio < ordenActual
        return (
          <button
            key={hijo.id}
            ref={esActual ? actualRef : undefined}
            className={`${styles.leaf} ${esActual ? styles.leafActual : ''} ${esPasado ? styles.leafPast : ''}`}
            onClick={() => onSelect(hijo.id)}
          >
            <span>{hijo.etiqueta}{esActual ? ' · actual' : ''}</span>
          </button>
        )
      })}
    </div>
  )
}