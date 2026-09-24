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
      <span aria-hidden="true">🔖</span>
      <span className={styles.label}>{guardado ? 'Guardado' : 'Guardar'}</span>
    </button>
  )
}