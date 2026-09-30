import { useRef, useState, type KeyboardEvent } from 'react'
import styles from './ComentarioForm.module.css'
import botones from '../../styles/botones.module.css'
import EmocionPopover from '../Emociones/EmocionPopover'
import AutocompleteDropdown from '../Autocomplete/AutocompleteDropdown'
import ReferenciaCruzadaAviso from '../ReferenciaCruzada/ReferenciaCruzadaAviso'
import NarrativaSelector, { NARRATIVA_VACIA, type NarrativaValue } from './NarrativaSelector'
import { useMentionHashtagAutocomplete } from '../../hooks/useMentionHashtagAutocomplete'
import {
  addComment,
  comentarioDesdeCreado,
  type AddCommentOptions,
  type CommentItem,
} from '../../api/comentarios'
import type { DeteccionCruzada } from '../../api/publicar'
import type { ObraDetalle } from '../../api/suscripciones'

type Variante = 'comentario' | 'respuesta'
type OverridesCruzada = Pick<AddCommentOptions, 'obraCruzadaId' | 'fronteraCruzadaId' | 'descartarReferenciaCruzada'>

interface Props {
  postId: number
  parentId?: number
  obraDetalle: ObraDetalle | null
  variante: Variante
  onCreado: (comentario: CommentItem) => void
}

const PLACEHOLDER: Record<Variante, string> = {
  comentario: 'Escribe un comentario...',
  respuesta: 'Escribe una respuesta...',
}

// Deja que el clic en el popover o el dropdown llegue antes de cerrarlos.
const RETARDO_BLUR_MS = 150

function mensajeDeError(error: unknown): string {
  const detalle = (error as { error?: unknown } | null)?.error
  return typeof detalle === 'string'
    ? detalle
    : 'No se pudo enviar. Revisa los datos e inténtalo de nuevo.'
}

export default function ComentarioForm({ postId, parentId, obraDetalle, variante, onCreado }: Props) {
  const [texto, setTexto] = useState('')
  const [emocion, setEmocion] = useState<string | null>(null)
  const [emocionAbierta, setEmocionAbierta] = useState(false)
  const [narrativa, setNarrativa] = useState<NarrativaValue>(NARRATIVA_VACIA)
  const [detecciones, setDetecciones] = useState<DeteccionCruzada[] | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const inputRef = useRef<HTMLInputElement>(null)
  const autocomplete = useMentionHashtagAutocomplete({ value: texto, onChange: setTexto, fieldRef: inputRef })

  const esRespuesta = variante === 'respuesta'

  async function enviar(overrides: OverridesCruzada = {}) {
    if (!texto.trim() || enviando) return

    setEnviando(true)
    setError(null)
    try {
      const resultado = await addComment(postId, texto, {
        parentId,
        emocionAutor: emocion,
        referenciaNarrativaId: narrativa.referenciaId,
        fronteraSpoilerId: narrativa.fronteraId,
        obraCruzadaId: narrativa.obraCruzadaId,
        fronteraCruzadaId: narrativa.fronteraCruzadaId,
        ...overrides,
      })

      if ('referenciaCruzadaDetectada' in resultado) {
        setDetecciones(resultado.detecciones)
        return
      }

      setDetecciones(null)
      setTexto('')
      setEmocion(null)
      setNarrativa(NARRATIVA_VACIA)
      onCreado(comentarioDesdeCreado(resultado))
    } catch (e) {
      setDetecciones(null)
      setError(mensajeDeError(e))
    } finally {
      setEnviando(false)
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (autocomplete.handleKeyDown(e)) return
    if (e.key === 'Enter') enviar()
  }

  function handleBlur() {
    setTimeout(() => {
      setEmocionAbierta(false)
      autocomplete.cerrar()
    }, RETARDO_BLUR_MS)
  }

  return (
    <div className={esRespuesta ? styles.formRespuesta : styles.formComentario}>
      <div className={styles.inputRow}>
        <div className={styles.inputWrap}>
          <input
            ref={inputRef}
            className={`${styles.input} ${esRespuesta ? styles.inputRespuesta : ''}`}
            type="text"
            value={texto}
            onChange={(e) => autocomplete.handleChange(e.target.value)}
            onFocus={() => setEmocionAbierta(true)}
            onBlur={handleBlur}
            onKeyDown={handleKeyDown}
            placeholder={PLACEHOLDER[variante]}
          />
          {autocomplete.suggestions.length > 0 ? (
            <AutocompleteDropdown
              suggestions={autocomplete.suggestions}
              activeIndex={autocomplete.activeIndex}
              onSelect={autocomplete.seleccionar}
            />
          ) : (
            <EmocionPopover visible={emocionAbierta} value={emocion} onSelect={setEmocion} />
          )}
        </div>

        <button
          className={esRespuesta ? styles.submitRespuesta : botones.primario}
          onClick={() => enviar()}
          disabled={enviando}
        >
          Enviar
        </button>
      </div>

      {error && <p className={styles.error}>{error}</p>}

      {obraDetalle && (
        <NarrativaSelector obraLocal={obraDetalle} value={narrativa} onChange={setNarrativa} />
      )}

      {detecciones && (
        <ReferenciaCruzadaAviso
          detecciones={detecciones}
          onConfirmar={(obraCruzadaId, fronteraCruzadaId) => enviar({ obraCruzadaId, fronteraCruzadaId })}
          onDescartar={() => enviar({ descartarReferenciaCruzada: true })}
          onCancelar={() => setDetecciones(null)}
        />
      )}
    </div>
  )
}