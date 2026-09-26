import { useRef, type Dispatch, type SetStateAction } from 'react'
import styles from './EdicionModal.module.css'
import AutocompleteDropdown from '../Autocomplete/AutocompleteDropdown'
import { useMentionHashtagAutocomplete } from '../../hooks/useMentionHashtagAutocomplete'

interface Props {
  id: string
  etiqueta: string
  value: string
  onChange: Dispatch<SetStateAction<string>>
}

// Deja que el clic en el dropdown llegue antes de cerrarlo.
const RETARDO_BLUR_MS = 150

export default function CampoTextoEdicion({ id, etiqueta, value, onChange }: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const autocomplete = useMentionHashtagAutocomplete({ value, onChange, fieldRef: textareaRef })

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
        onBlur={() => setTimeout(autocomplete.cerrar, RETARDO_BLUR_MS)}
      />
      <AutocompleteDropdown
        suggestions={autocomplete.suggestions}
        activeIndex={autocomplete.activeIndex}
        onSelect={autocomplete.seleccionar}
      />
    </div>
  )
}