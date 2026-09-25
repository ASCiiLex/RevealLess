import { useMemo, useRef, useState, type KeyboardEvent } from 'react'
import styles from './EditCommentForm.module.css'
import { updateComment, type CommentItem } from '../../api/postDetail'
import type { ObraDetalle } from '../../api/suscripciones'
import EmocionSelector from '../Emociones/EmocionSelector'
import NarrativaSelector, { type NarrativaValue } from './NarrativaSelector'
import { useMentionHashtagAutocomplete } from '../../hooks/useMentionHashtagAutocomplete'
import AutocompleteDropdown from '../Autocomplete/AutocompleteDropdown'

interface Props {
  comment: CommentItem
  obraDetalle: ObraDetalle | null
  onGuardado: (datos: { text: string; emocion_autor: string | null }) => void
  onCancelar: () => void
}

export default function EditCommentForm({ comment, obraDetalle, onGuardado, onCancelar }: Props) {
  const [text, setText] = useState(comment.text)
  const [narrativa, setNarrativa] = useState<NarrativaValue>({
    referenciaId: comment.referencia_narrativa_id,
    fronteraId: null,
    obraCruzadaId: comment.obra_cruzada_id,
    fronteraCruzadaId: null,
  })
  const [emocionAutor, setEmocionAutor] = useState<string | null>(comment.emocion_autor)
  const [error, setError] = useState<string | null>(null)
  const [avisoReduccion, setAvisoReduccion] = useState<string | null>(null)
  const [confirmadoPeseAviso, setConfirmadoPeseAviso] = useState(false)
  const [guardando, setGuardando] = useState(false)

  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const autocomplete = useMentionHashtagAutocomplete({ value: text, onChange: setText, fieldRef: textareaRef })

  const unidadPorId = useMemo(() => {
    const mapa = new Map<number, { orden_inicio: number }>()
    obraDetalle?.unidades.forEach((u) => mapa.set(u.id, u))
    return mapa
  }, [obraDetalle])

  function detectarReduccion(): string | null {
    const avisos: string[] = []
    const referenciaOriginal = comment.referencia_narrativa_id ? unidadPorId.get(comment.referencia_narrativa_id) : null
    const fronteraOriginal = comment.frontera_spoiler_id ? unidadPorId.get(comment.frontera_spoiler_id) : null

    if (
      narrativa.referenciaId &&
      referenciaOriginal &&
      narrativa.referenciaId !== comment.referencia_narrativa_id
    ) {
      const nuevaUnidad = unidadPorId.get(narrativa.referenciaId)
      if (nuevaUnidad && nuevaUnidad.orden_inicio < referenciaOriginal.orden_inicio) {
        avisos.push('estás moviendo la referencia narrativa hacia atrás')
      }
    }

    if (narrativa.fronteraId && fronteraOriginal) {
      const nuevaFrontera = unidadPorId.get(narrativa.fronteraId)
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
        referenciaNarrativaId: narrativa.referenciaId ?? undefined,
        fronteraSpoilerId: narrativa.fronteraId ?? undefined,
        obraCruzadaId: narrativa.obraCruzadaId ?? undefined,
        fronteraCruzadaId: narrativa.fronteraCruzadaId ?? undefined,
      })
      onGuardado({ text, emocion_autor: emocionAutor })
    } catch {
      setError('No se pudo guardar la edición. Revisa los datos e inténtalo de nuevo.')
    } finally {
      setGuardando(false)
    }
  }

  function handleKeyDownTexto(e: KeyboardEvent<HTMLTextAreaElement>) {
    autocomplete.handleKeyDown(e)
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

          <div className={styles.field} style={{ position: 'relative' }}>
            <label className={styles.label} htmlFor="edit-comment-text">¿Qué quieres comentar?</label>
            <textarea
              id="edit-comment-text"
              ref={textareaRef}
              className={styles.textarea}
              value={text}
              onChange={(e) => autocomplete.handleChange(e.target.value)}
              onKeyDown={handleKeyDownTexto}
              onBlur={() => setTimeout(autocomplete.cerrar, 150)}
            />
            <AutocompleteDropdown
              suggestions={autocomplete.suggestions}
              activeIndex={autocomplete.activeIndex}
              onSelect={autocomplete.seleccionar}
            />
          </div>

          <NarrativaSelector
            obraLocal={obraDetalle}
            value={narrativa}
            onChange={(v) => {
              setNarrativa(v)
              setConfirmadoPeseAviso(false)
            }}
          />

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