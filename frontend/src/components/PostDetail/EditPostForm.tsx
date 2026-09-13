import { useEffect, useState } from 'react'
import styles from './EditPostForm.module.css'
import { fetchObraDetalle, type ObraDetalle } from '../../api/suscripciones'
import { updatePost } from '../../api/postDetail'
import type { FeedPost } from '../../api/feed'

interface Props {
  post: FeedPost
  onGuardado: (post: FeedPost) => void
  onCancelar: () => void
}

export default function EditPostForm({ post, onGuardado, onCancelar }: Props) {
  const [detalle, setDetalle] = useState<ObraDetalle | null>(null)
  const [text, setText] = useState(post.text)
  const [referenciaId, setReferenciaId] = useState(post.referencia_narrativa?.id ?? null)
  const [fronteraId, setFronteraId] = useState<number | null>(null)
  const [nivelSpoiler, setNivelSpoiler] = useState(post.nivel_spoiler)
  const [error, setError] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    fetchObraDetalle(post.obra_slug).then(setDetalle)
  }, [post.obra_slug])

  async function handleGuardar() {
    setError(null)
    setGuardando(true)
    try {
      const actualizado = await updatePost(post.id, {
        text,
        referenciaNarrativaId: referenciaId ?? undefined,
        fronteraSpoilerId: fronteraId ?? undefined,
        nivelSpoiler,
      })
      onGuardado(actualizado)
    } catch {
      setError('No se pudo guardar la edición. Revisa los datos e inténtalo de nuevo.')
    } finally {
      setGuardando(false)
    }
  }

  if (!detalle) {
    return null
  }

  return (
    <div className={styles.overlay} onClick={onCancelar}>
      <div className={styles.panel} onClick={(e) => e.stopPropagation()}>
        <h2 className={styles.title}>Editar publicación</h2>

        <div className={styles.form}>
          {error && <p className={styles.error}>{error}</p>}

          <div className={styles.field}>
            <label className={styles.label} htmlFor="edit-text">Texto</label>
            <textarea
              id="edit-text"
              className={styles.textarea}
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="edit-referencia">¿De qué parte habla?</label>
            <select
              id="edit-referencia"
              className={styles.select}
              value={referenciaId ?? ''}
              onChange={(e) => setReferenciaId(Number(e.target.value) || null)}
            >
              {detalle.unidades.map((u) => (
                <option key={u.id} value={u.id}>{u.etiqueta}</option>
              ))}
            </select>
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="edit-frontera">
              Frontera de spoiler (déjalo vacío para no cambiarla)
            </label>
            <select
              id="edit-frontera"
              className={styles.select}
              value={fronteraId ?? ''}
              onChange={(e) => setFronteraId(Number(e.target.value) || null)}
            >
              <option value="">No cambiar</option>
              {detalle.unidades.map((u) => (
                <option key={u.id} value={u.id}>{u.etiqueta}</option>
              ))}
            </select>
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="edit-nivel">Nivel de spoiler</label>
            <select
              id="edit-nivel"
              className={styles.select}
              value={nivelSpoiler}
              onChange={(e) => setNivelSpoiler(e.target.value)}
            >
              <option value="menor">Menor</option>
              <option value="importante">Importante</option>
              <option value="trama_central">Trama central</option>
            </select>
          </div>

          <div className={styles.actions}>
            <button className={`${styles.button} ${styles.cancel}`} onClick={onCancelar}>
              Cancelar
            </button>
            <button
              className={`${styles.button} ${styles.confirm}`}
              onClick={handleGuardar}
              disabled={guardando || !text.trim()}
            >
              {guardando ? 'Guardando...' : 'Guardar cambios'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}