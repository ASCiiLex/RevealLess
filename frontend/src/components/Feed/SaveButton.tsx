import { useState } from 'react'
import styles from './SaveButton.module.css'
import { guardarPost, quitarGuardado } from '../../api/savedPosts'

interface Props {
  postId: number
  guardadoInicial: boolean
}

export default function SaveButton({ postId, guardadoInicial }: Props) {
  const [guardado, setGuardado] = useState(guardadoInicial)
  const [cargando, setCargando] = useState(false)

  async function handleClick() {
    if (cargando) return
    setCargando(true)
    try {
      const estado = guardado ? await quitarGuardado(postId) : await guardarPost(postId)
      setGuardado(estado.is_saved)
    } catch {
      // Sin cambios: el botón conserva su estado anterior.
    } finally {
      setCargando(false)
    }
  }

  return (
    <button
      type="button"
      className={`${styles.save} ${guardado ? styles.saveActive : ''}`}
      onClick={handleClick}
      disabled={cargando}
      aria-pressed={guardado}
      aria-label={guardado ? 'Quitar de guardados' : 'Guardar publicación'}
    >
      <svg
        className={styles.icon}
        viewBox="0 0 24 24"
        width="14"
        height="14"
        aria-hidden="true"
        fill={guardado ? 'currentColor' : 'none'}
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      >
        <path d="M6 3h12a1 1 0 0 1 1 1v17l-7-4-7 4V4a1 1 0 0 1 1-1z" />
      </svg>
      <span className={styles.label}>{guardado ? 'Guardado' : 'Guardar'}</span>
    </button>
  )
}