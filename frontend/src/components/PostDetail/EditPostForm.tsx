import { useEffect, useState } from 'react'
import styles from './EdicionModal.module.css'
import EdicionModal from './EdicionModal'
import CampoTextoEdicion from './CampoTextoEdicion'
import EmocionSelector from '../Emociones/EmocionSelector'
import { fetchObraDetalle, type ObraDetalle } from '../../api/suscripciones'
import { updatePost } from '../../api/postDetail'
import { useAvisoConfirmable } from '../../hooks/useAvisoConfirmable'
import { detectarReduccion } from '../../utils/avisoReduccion'
import type { FeedPost } from '../../api/feed'

interface Props {
  post: FeedPost
  onGuardado: (post: FeedPost) => void
  onCancelar: () => void
}

const NIVELES_SPOILER = [
  { valor: 'menor', etiqueta: 'Menor' },
  { valor: 'importante', etiqueta: 'Importante' },
  { valor: 'trama_central', etiqueta: 'Trama central' },
]

const ERROR_GUARDADO = 'No se pudo guardar la edición. Revisa los datos e inténtalo de nuevo.'

export default function EditPostForm({ post, onGuardado, onCancelar }: Props) {
  const [detalle, setDetalle] = useState<ObraDetalle | null>(null)
  const [text, setText] = useState(post.text)
  const [referenciaId, setReferenciaId] = useState(post.referencia_narrativa?.id ?? null)
  const [fronteraId, setFronteraId] = useState<number | null>(null)
  const [nivelSpoiler, setNivelSpoiler] = useState(post.nivel_spoiler)
  const [emocionAutor, setEmocionAutor] = useState<string | null>(post.emocion_autor)
  const [error, setError] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)
  const aviso = useAvisoConfirmable()

  useEffect(() => {
    fetchObraDetalle(post.obra_slug).then(setDetalle)
  }, [post.obra_slug])

  async function handleGuardar() {
    if (!detalle) return
    setError(null)

    const bloqueado = aviso.bloquea(detectarReduccion({
      unidades: detalle.unidades,
      referenciaOriginalId: post.referencia_narrativa?.id ?? null,
      referenciaNuevaId: referenciaId,
      fronteraOriginalId: post.frontera_spoiler?.id ?? null,
      fronteraNuevaId: fronteraId,
    }))
    if (bloqueado) return

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
      setError(ERROR_GUARDADO)
    } finally {
      setGuardando(false)
    }
  }

  if (!detalle) {
    return null
  }

  return (
    <EdicionModal
      titulo="Editar publicación"
      error={error}
      aviso={aviso.aviso}
      onConfirmarAviso={aviso.confirmar}
      guardando={guardando}
      puedeGuardar={text.trim().length > 0}
      onGuardar={handleGuardar}
      onCancelar={onCancelar}
    >
      <CampoTextoEdicion id="edit-text" etiqueta="Texto" value={text} onChange={setText} />

      <EmocionSelector value={emocionAutor} onChange={setEmocionAutor} colapsable={false} />

      <div className={styles.field}>
        <label className={styles.label} htmlFor="edit-referencia">¿De qué parte habla?</label>
        <select
          id="edit-referencia"
          className={styles.select}
          value={referenciaId ?? ''}
          onChange={(e) => {
            setReferenciaId(Number(e.target.value) || null)
            aviso.reiniciar()
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
            aviso.reiniciar()
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
          {NIVELES_SPOILER.map((n) => (
            <option key={n.valor} value={n.valor}>{n.etiqueta}</option>
          ))}
        </select>
      </div>
    </EdicionModal>
  )
}