import { useState } from 'react'
import styles from './ReactionBar.module.css'
import { toggleReactionPost } from '../../api/postDetail'

const REACCIONES: { tipo: string; emoji: string }[] = [
  { tipo: 'like', emoji: '👍' },
  { tipo: 'love', emoji: '❤️' },
  { tipo: 'funny', emoji: '😂' },
  { tipo: 'wow', emoji: '😮' },
  { tipo: 'sad', emoji: '😢' },
]

interface Props {
  postId: number
  reaccionInicial: string | null
  contadorInicial: number
}

export default function ReactionBar({ postId, reaccionInicial, contadorInicial }: Props) {
  const [reaccion, setReaccion] = useState(reaccionInicial)
  const [contador, setContador] = useState(contadorInicial)

  async function handleReaccion(tipo: string) {
    const resultado = await toggleReactionPost(postId, tipo)
    setReaccion(resultado.removed ? null : tipo)
    setContador(resultado.count)
  }

  return (
    <div className={styles.bar}>
      {REACCIONES.map((r) => (
        <button
          key={r.tipo}
          className={`${styles.reactionButton} ${reaccion === r.tipo ? styles.reactionButtonActive : ''}`}
          onClick={() => handleReaccion(r.tipo)}
          aria-label={r.tipo}
        >
          {r.emoji}
        </button>
      ))}
      {contador > 0 && <span className={styles.count}>{contador}</span>}
    </div>
  )
}