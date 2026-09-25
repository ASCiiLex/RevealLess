import { useEffect, useRef, useState } from 'react'
import styles from './ReactionBar.module.css'
import { toggleReactionPost, toggleReactionComment, toggleReactionMessage, fetchPostReactionsTotals } from '../../api/postDetail'
import { EMOCIONES } from '../../constants/emociones'

interface Props {
  targetId: number
  target?: 'post' | 'comment' | 'message'
  reaccionInicial: string | null
  totalesEnVivo?: Record<string, number>
  variante?: 'normal' | 'sutil'
}

async function fetchCommentReactionsTotals(commentId: number): Promise<{ totals: Record<string, number> }> {
  const response = await fetch(`/comments/reactions/${commentId}/`, {
    credentials: 'same-origin',
  })
  return response.json()
}

async function fetchMessageReactionsTotals(messageId: number): Promise<{ totals: Record<string, number> }> {
  const response = await fetch(`/mensajes/${messageId}/reactions/`, {
    credentials: 'same-origin',
  })
  return response.json()
}

export default function ReactionBar({
  targetId,
  target = 'post',
  reaccionInicial,
  totalesEnVivo,
  variante = 'normal',
}: Props) {
  const [reaccion, setReaccion] = useState(reaccionInicial)
  const [totales, setTotales] = useState<Record<string, number>>({})
  const [abierto, setAbierto] = useState(false)
  const [posicion, setPosicion] = useState<'abajo' | 'arriba'>('abajo')
  const wrapperRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const fetchTotales =
      target === 'post' ? fetchPostReactionsTotals :
      target === 'comment' ? fetchCommentReactionsTotals :
      fetchMessageReactionsTotals
    fetchTotales(targetId).then((data) => setTotales(data.totals))
  }, [targetId, target])

  useEffect(() => {
    if (totalesEnVivo) {
      setTotales(totalesEnVivo)
    }
  }, [totalesEnVivo])

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setAbierto(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function handleAbrir() {
    if (!abierto && wrapperRef.current) {
      const rect = wrapperRef.current.getBoundingClientRect()
      const espacioAbajo = window.innerHeight - rect.bottom - 64
      setPosicion(espacioAbajo < 160 ? 'arriba' : 'abajo')
    }
    setAbierto((v) => !v)
  }

  async function handleReaccion(tipo: string) {
    const resultado =
      target === 'post' ? await toggleReactionPost(targetId, tipo) :
      target === 'comment' ? await toggleReactionComment(targetId, tipo) :
      await toggleReactionMessage(targetId, tipo)
    setReaccion(resultado.removed ? null : tipo)
    setTotales(resultado.counts)
    setAbierto(false)
  }

  async function handleQuitar() {
    if (!reaccion) return
    await handleReaccion(reaccion)
  }

  const emocionActual = EMOCIONES.find((e) => e.clave === reaccion)
  const contadorPropio = reaccion ? (totales[reaccion] ?? 0) : 0
  const totalGlobal = Object.values(totales).reduce((suma, n) => suma + n, 0)

  return (
    <div className={styles.wrapper} ref={wrapperRef}>
      <button
        className={`${styles.trigger} ${variante === 'sutil' ? styles.triggerSutil : ''} ${reaccion ? styles.triggerActive : ''}`}
        onClick={handleAbrir}
        aria-expanded={abierto}
      >
        <span className={styles.triggerEmoji} aria-hidden="true">
          {emocionActual ? emocionActual.emoji : '🤍'}
        </span>
        <span>{emocionActual ? emocionActual.etiqueta : 'Reaccionar'}</span>
        {reaccion && <span className={styles.triggerCount}>· {contadorPropio}</span>}
      </button>

      {totalGlobal > 0 && (
        <span className={styles.totalGlobal}>{totalGlobal} en total</span>
      )}

      {abierto && (
        <div className={`${styles.panel} ${posicion === 'arriba' ? styles.panelArriba : ''}`}>
          <div className={styles.grid}>
            {EMOCIONES.map((e) => (
              <button
                key={e.clave}
                className={`${styles.opcion} ${reaccion === e.clave ? styles.opcionActiva : ''}`}
                onClick={() => handleReaccion(e.clave)}
                aria-label={e.etiqueta}
                title={e.etiqueta}
              >
                <span className={styles.opcionEmoji}>{e.emoji}</span>
                {totales[e.clave] > 0 && (
                  <span className={styles.opcionContador}>{totales[e.clave]}</span>
                )}
              </button>
            ))}
          </div>
          {reaccion && (
            <button className={styles.quitar} onClick={handleQuitar}>
              Quitar mi reacción ({emocionActual?.etiqueta})
            </button>
          )}
        </div>
      )}
    </div>
  )
}