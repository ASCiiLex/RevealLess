import { useEffect, useMemo, useState } from 'react'
import styles from './EditPostForm.module.css'
import { fetchObraDetalle, type ObraDetalle } from '../../api/suscripciones'
import { updatePost } from '../../api/postDetail'
import EmocionSelector from '../Emociones/EmocionSelector'
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
  const [emocionAutor, setEmocionAutor] = useState<string | null>(post.emocion_autor)
  const [error, setError] = useState<string | null>(null)
  const [avisoReduccion, setAvisoReduccion] = useState<string | null>(null)
  const [confirmadoPeseAviso, setConfirmadoPeseAviso] = useState(false)
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    fetchObraDetalle(post.obra_slug).then(setDetalle)
  }, [post.obra_slug])

  const unidadPorId = useMemo(() => {
    const mapa = new Map<number, { orden_inicio: number }>()
    detalle?.unidades.forEach((u) => mapa.set(u.id, u))
    return mapa
  }, [detalle])

  function detectarReduccion(): string | null {
    const avisos: string[] = []

    if (
      referenciaId &&
      post.referencia_narrativa &&
      referenciaId !== post.referencia_narrativa.id
    ) {
      const nuevaUnidad = unidadPorId.get(referenciaId)
      if (nuevaUnidad && nuevaUnidad.orden_inicio < post.referencia_narrativa.orden_inicio) {
        avisos.push('estás moviendo la referencia narrativa hacia atrás')
      }
    }

    if (fronteraId && post.frontera_spoiler) {
      const nuevaFrontera = unidadPorId.get(fronteraId)
      if (nuevaFrontera && nuevaFrontera.orden_inicio < post.frontera_spoiler.orden_inicio) {
        avisos.push('estás reduciendo la frontera de spoiler')
      }
    }

    if (avisos.length === 0) return null
    return `Atención: ${avisos.join(' y ')}. Esto no oculta el contenido a lectores que ya lo hayan visto con los valores anteriores, más permisivos desde ahora en adelante.`
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
      const actualizado = await updatePost(post.id, {
        text,
        referenciaNarrativaId: referenciaId ?? undefined,
        fronteraSpoilerId: fronteraId ?? undefined,
        nivelSpoiler,
        emocionAutor,
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
            <label className={styles.label} htmlFor="edit-text">Texto</label>
            <textarea
              id="edit-text"
              className={styles.textarea}
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          </div>

          <EmocionSelector value={emocionAutor} onChange={setEmocionAutor} />

          <div className={styles.field}>
            <label className={styles.label} htmlFor="edit-referencia">¿De qué parte habla?</label>
            <select
              id="edit-referencia"
              className={styles.select}
              value={referenciaId ?? ''}
              onChange={(e) => {
                setReferenciaId(Number(e.target.value) || null)
                setConfirmadoPeseAviso(false)
              }}
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
              onChange={(e) => {
                setFronteraId(Number(e.target.value) || null)
                setConfirmadoPeseAviso(false)
              }}
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