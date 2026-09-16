import { useMemo, useState } from 'react'
import styles from './EditCommentForm.module.css'
import { updateComment, type CommentItem } from '../../api/postDetail'
import type { ObraDetalle } from '../../api/suscripciones'
import EmocionSelector from '../Emociones/EmocionSelector'

interface Props {
  comment: CommentItem
  obraDetalle: ObraDetalle | null
  onGuardado: (datos: { text: string; emocion_autor: string | null }) => void
  onCancelar: () => void
}

export default function EditCommentForm({ comment, obraDetalle, onGuardado, onCancelar }: Props) {
  const [text, setText] = useState(comment.text)
  const [referenciaId, setReferenciaId] = useState(comment.referencia_narrativa_id)
  const [fronteraId, setFronteraId] = useState<number | null>(null)
  const [emocionAutor, setEmocionAutor] = useState<string | null>(comment.emocion_autor)
  const [error, setError] = useState<string | null>(null)
  const [avisoReduccion, setAvisoReduccion] = useState<string | null>(null)
  const [confirmadoPeseAviso, setConfirmadoPeseAviso] = useState(false)
  const [guardando, setGuardando] = useState(false)

  const unidadPorId = useMemo(() => {
    const mapa = new Map<number, { orden_inicio: number }>()
    obraDetalle?.unidades.forEach((u) => mapa.set(u.id, u))
    return mapa
  }, [obraDetalle])

  function detectarReduccion(): string | null {
    const avisos: string[] = []
    const referenciaOriginal = comment.referencia_narrativa_id ? unidadPorId.get(comment.referencia_narrativa_id) : null
    const fronteraOriginal = comment.frontera_spoiler_id ? unidadPorId.get(comment.frontera_spoiler_id) : null

    if (referenciaId && referenciaOriginal && referenciaId !== comment.referencia_narrativa_id) {
      const nuevaUnidad = unidadPorId.get(referenciaId)
      if (nuevaUnidad && nuevaUnidad.orden_inicio < referenciaOriginal.orden_inicio) {
        avisos.push('estás moviendo la referencia narrativa hacia atrás')
      }
    }

    if (fronteraId && fronteraOriginal) {
      const nuevaFrontera = unidadPorId.get(fronteraId)
      if (nuevaFrontera && nuevaFrontera.orden_inicio < fronteraOriginal.orden_inicio) {
        avisos.push('estás reduciendo la frontera de spoiler')
      }
    }

    if (avisos.length === 0) return null
    return `Atención: ${avisos.join(' y ')}. Esto no oculta el contenido a lectores que ya lo hayan visto con los valores anteriores.`
  }

  async function handleGuardar() {
    setError(null)

    if (!confirmadoPeseAviso) {
      const aviso = detectarReduccion()
      if (aviso) {
        setAvisoReduccion(aviso)
        return
      }
    }

    setGuardando(true)
    try {
      await updateComment(comment.id, {
        text,
        emocionAutor: emocionAutor,
        referenciaNarrativaId: referenciaId ?? undefined,
        fronteraSpoilerId: fronteraId ?? undefined,
      })
      onGuardado({ text, emocion_autor: emocionAutor })
    } catch {
      setError('No se pudo guardar la edición. Revisa los datos e inténtalo de nuevo.')
    } finally {
      setGuardando(false)
    }
  }

  if (!obraDetalle) {
    return null
  }

  return (
    <div className={styles.overlay} onClick={onCancelar}>
      <div className={styles.panel} onClick={(e) => e.stopPropagation()}>
        <h2 className={styles.title}>Editar comentario</h2>

        <div className={styles.form}>
          {error && <p className={styles.error}>{error}</p>}

          {avisoReduccion && (
            <div className={styles.warningBox}>
              {avisoReduccion}
              <br />
              <button
                className={styles.confirmLink}
                onClick={() => {
                  setConfirmadoPeseAviso(true)
                  setAvisoReduccion(null)
                }}
              >
                Entiendo, continuar de todas formas
              </button>
            </div>
          )}

          <div className={styles.field}>
            <label className={styles.label} htmlFor="edit-comment-text">¿Qué quieres comentar?</label>
            <textarea
              id="edit-comment-text"
              className={styles.textarea}
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="edit-comment-referencia">
              ¿De qué parte trata el comentario? (opcional)
            </label>
            <select
              id="edit-comment-referencia"
              className={styles.select}
              value={referenciaId ?? ''}
              onChange={(e) => {
                setReferenciaId(Number(e.target.value) || null)
                setConfirmadoPeseAviso(false)
              }}
            >
              <option value="">Sin cambiar</option>
              {obraDetalle.unidades.map((u) => (
                <option key={u.id} value={u.id}>{u.etiqueta}</option>
              ))}
            </select>
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="edit-comment-frontera">
              ¿Hasta dónde hay que haber visto/leído? (opcional)
            </label>
            <select
              id="edit-comment-frontera"
              className={styles.select}
              value={fronteraId ?? ''}
              onChange={(e) => {
                setFronteraId(Number(e.target.value) || null)
                setConfirmadoPeseAviso(false)
              }}
            >
              <option value="">No cambiar</option>
              {obraDetalle.unidades.map((u) => (
                <option key={u.id} value={u.id}>{u.etiqueta}</option>
              ))}
            </select>
          </div>

          <EmocionSelector
            value={emocionAutor}
            onChange={setEmocionAutor}
            label="¿Quieres añadir emoción de contexto? (opcional)"
          />

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