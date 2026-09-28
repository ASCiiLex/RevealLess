import { useRef, useState, type Dispatch, type SetStateAction } from 'react'
import styles from './EdicionModal.module.css'
import AutocompleteDropdown from '../Autocomplete/AutocompleteDropdown'
import EmocionPopover from '../Emociones/EmocionPopover'
import EmocionChip from '../Emociones/EmocionChip'
import { useMentionHashtagAutocomplete } from '../../hooks/useMentionHashtagAutocomplete'

interface Props {
  id: string
  etiqueta: string
  value: string
  onChange: Dispatch<SetStateAction<string>>
  emocion?: string | null
  onEmocionChange?: (clave: string | null) => void
}

// Deja que el clic en el popover o el dropdown llegue antes de cerrarlos.
const RETARDO_BLUR_MS = 150

export default function CampoTextoEdicion({ id, etiqueta, value, onChange, emocion = null, onEmocionChange }: Props) {
  const [emocionAbierta, setEmocionAbierta] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const autocomplete = useMentionHashtagAutocomplete({ value, onChange, fieldRef: textareaRef })

  function handleBlur() {
    setTimeout(() => {
      autocomplete.cerrar()
      setEmocionAbierta(false)
    }, RETARDO_BLUR_MS)
  }

  return (
    <div className={`${styles.field} ${styles.fieldRelativo}`}>
      <label className={styles.label} htmlFor={id}>{etiqueta}</label>
      <textarea
        id={id}
        ref={textareaRef}
        className={styles.textarea}
        value={value}
        onChange={(e) => autocomplete.handleChange(e.target.value)}
        onKeyDown={autocomplete.handleKeyDown}
        onFocus={() => setEmocionAbierta(true)}
        onBlur={handleBlur}
      />
      {autocomplete.suggestions.length > 0 ? (
        <AutocompleteDropdown
          suggestions={autocomplete.suggestions}
          activeIndex={autocomplete.activeIndex}
          onSelect={autocomplete.seleccionar}
        />
      ) : (
        onEmocionChange && (
          <EmocionPopover visible={emocionAbierta} value={emocion} onSelect={onEmocionChange} direccion="abajo" />
        )
      )}
      {onEmocionChange && <EmocionChip value={emocion} onQuitar={() => onEmocionChange(null)} />}
    </div>
  )
}