import { useEffect, useRef, useState, type Dispatch, type SetStateAction } from 'react'
import styles from './EditorTexto.module.css'
import AutocompleteDropdown from '../Autocomplete/AutocompleteDropdown'
import EmocionPopover from '../Emociones/EmocionPopover'
import { EMOCIONES } from '../../constants/emociones'
import { fetchSuggestedHashtags } from '../../api/textAutocomplete'
import { useMentionHashtagAutocomplete } from '../../hooks/useMentionHashtagAutocomplete'

interface Props {
  id: string
  texto: string
  onTextoChange: Dispatch<SetStateAction<string>>
  emocion: string | null
  onEmocionChange: (emocion: string | null) => void
  imagen: File | null
  onImagenChange: (imagen: File | null) => void
}

// Deja que el clic en el popover o el dropdown llegue antes de cerrarlos.
const RETARDO_BLUR_MS = 150
const TIPOS_IMAGEN = 'image/jpeg,image/png,image/webp'

export default function EditorTexto({
  id, texto, onTextoChange, emocion, onEmocionChange, imagen, onImagenChange,
}: Props) {
  const [emocionAbierta, setEmocionAbierta] = useState(false)
  const [hashtagsSugeridos, setHashtagsSugeridos] = useState<string[]>([])

  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const autocomplete = useMentionHashtagAutocomplete({ value: texto, onChange: onTextoChange, fieldRef: textareaRef })

  useEffect(() => {
    fetchSuggestedHashtags().then((data) => setHashtagsSugeridos(data.results))
  }, [])

  function insertarHashtag(tag: string) {
    const campo = textareaRef.current
    const insertado = `#${tag} `
    const cursor = campo?.selectionStart ?? texto.length
    onTextoChange(texto.slice(0, cursor) + insertado + texto.slice(cursor))
    requestAnimationFrame(() => {
      const pos = cursor + insertado.length
      campo?.setSelectionRange(pos, pos)
      campo?.focus()
    })
  }

  function handleBlur() {
    setTimeout(() => {
      autocomplete.cerrar()
      setEmocionAbierta(false)
    }, RETARDO_BLUR_MS)
  }

  const emocionActual = EMOCIONES.find((e) => e.clave === emocion)

  return (
    <div className={styles.box}>
      <div className={styles.textareaWrap}>
        <textarea
          id={id}
          ref={textareaRef}
          className={styles.textarea}
          value={texto}
          onChange={(e) => autocomplete.handleChange(e.target.value)}
          onKeyDown={autocomplete.handleKeyDown}
          onFocus={() => setEmocionAbierta(true)}
          onBlur={handleBlur}
          required
        />
        <AutocompleteDropdown
          suggestions={autocomplete.suggestions}
          activeIndex={autocomplete.activeIndex}
          onSelect={autocomplete.seleccionar}
        />
        <EmocionPopover visible={emocionAbierta} value={emocion} onSelect={onEmocionChange} />
      </div>

      {hashtagsSugeridos.length > 0 && (
        <div className={styles.hashtagsSugeridos}>
          {hashtagsSugeridos.map((tag) => (
            <button key={tag} type="button" className={styles.chip} onClick={() => insertarHashtag(tag)}>
              #{tag}
            </button>
          ))}
        </div>
      )}

      <div className={styles.footer}>
        {emocionActual && (
          <span className={styles.emocionElegida}>
            {emocionActual.emoji} {emocionActual.etiqueta}
            <button type="button" className={styles.emocionQuitar} onClick={() => onEmocionChange(null)}>×</button>
          </span>
        )}
        <button type="button" className={styles.chip} onClick={() => fileInputRef.current?.click()}>
          {imagen ? imagen.name : '📷 Añadir imagen'}
        </button>
        <input
          ref={fileInputRef}
          className={styles.inputOculto}
          type="file"
          accept={TIPOS_IMAGEN}
          onChange={(e) => onImagenChange(e.target.files?.[0] ?? null)}
        />
      </div>
    </div>
  )
}