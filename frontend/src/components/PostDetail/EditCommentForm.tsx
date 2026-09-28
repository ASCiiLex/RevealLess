import { useState } from 'react'
import EdicionModal from './EdicionModal'
import CampoTextoEdicion from './CampoTextoEdicion'
import NarrativaSelector, { type NarrativaValue } from './NarrativaSelector'
import { updateComment, type CommentItem, type CommentUpdate } from '../../api/comentarios'
import type { ObraDetalle } from '../../api/suscripciones'
import { useAvisoConfirmable } from '../../hooks/useAvisoConfirmable'
import { detectarReduccion } from '../../utils/avisoReduccion'

interface Props {
  comment: CommentItem
  obraDetalle: ObraDetalle | null
  onGuardado: (datos: { text: string; emocion_autor: string | null }) => void
  onCancelar: () => void
}

const ERROR_GUARDADO = 'No se pudo guardar la edición. Revisa los datos e inténtalo de nuevo.'

function cambiosCruzada(comment: CommentItem, narrativa: NarrativaValue): Pick<CommentUpdate, 'obraCruzadaId' | 'fronteraCruzadaId'> {
  // Tenía obra cruzada y el usuario eligió "Esta obra": se vacían ambos campos.
  if (narrativa.obraCruzadaId === null && comment.obra_cruzada_id !== null) {
    return { obraCruzadaId: null, fronteraCruzadaId: null }
  }
  return {
    obraCruzadaId: narrativa.obraCruzadaId ?? undefined,
    fronteraCruzadaId: narrativa.fronteraCruzadaId ?? undefined,
  }
}

export default function EditCommentForm({ comment, obraDetalle, onGuardado, onCancelar }: Props) {
  const [text, setText] = useState(comment.text)
  const [narrativa, setNarrativa] = useState<NarrativaValue>({
    referenciaId: comment.referencia_narrativa_id,
    fronteraId: null,
    obraCruzadaId: comment.obra_cruzada_id,
    fronteraCruzadaId: comment.frontera_cruzada_id,
  })
  const [emocionAutor, setEmocionAutor] = useState<string | null>(comment.emocion_autor)
  const [error, setError] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)
  const aviso = useAvisoConfirmable()

  async function handleGuardar() {
    if (!obraDetalle) return
    setError(null)

    const bloqueado = aviso.bloquea(detectarReduccion({
      unidades: obraDetalle.unidades,
      referenciaOriginalId: comment.referencia_narrativa_id,
      referenciaNuevaId: narrativa.referenciaId,
      fronteraOriginalId: comment.frontera_spoiler_id,
      fronteraNuevaId: narrativa.fronteraId,
    }))
    if (bloqueado) return

    setGuardando(true)
    try {
      await updateComment(comment.id, {
        text,
        emocionAutor,
        referenciaNarrativaId: narrativa.referenciaId ?? undefined,
        fronteraSpoilerId: narrativa.fronteraId ?? undefined,
        ...cambiosCruzada(comment, narrativa),
      })
      onGuardado({ text, emocion_autor: emocionAutor })
    } catch {
      setError(ERROR_GUARDADO)
    } finally {
      setGuardando(false)
    }
  }

  if (!obraDetalle) {
    return null
  }

  return (
    <EdicionModal
      titulo="Editar comentario"
      error={error}
      aviso={aviso.aviso}
      onConfirmarAviso={aviso.confirmar}
      guardando={guardando}
      puedeGuardar={text.trim().length > 0}
      onGuardar={handleGuardar}
      onCancelar={onCancelar}
    >
      <CampoTextoEdicion
        id="edit-comment-text"
        etiqueta="¿Qué quieres comentar?"
        value={text}
        onChange={setText}
        emocion={emocionAutor}
        onEmocionChange={setEmocionAutor}
      />

      <NarrativaSelector
        obraLocal={obraDetalle}
        value={narrativa}
        onChange={(v) => {
          setNarrativa(v)
          aviso.reiniciar()
        }}
      />
    </EdicionModal>
  )
}