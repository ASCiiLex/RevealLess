import styles from './AutocompleteDropdown.module.css'
import type { AutocompleteSuggestion } from '../../hooks/useMentionHashtagAutocomplete'

interface Props {
  suggestions: AutocompleteSuggestion[]
  activeIndex: number
  onSelect: (s: AutocompleteSuggestion) => void
}

export default function AutocompleteDropdown({ suggestions, activeIndex, onSelect }: Props) {
  if (suggestions.length === 0) return null

  return (
    <div className={styles.dropdown} role="listbox">
      {suggestions.map((s, i) => (
        <button
          key={`${s.trigger}${s.value}`}
          type="button"
          role="option"
          aria-selected={i === activeIndex}
          className={`${styles.item} ${i === activeIndex ? styles.itemActive : ''}`}
          onMouseDown={(e) => {
            e.preventDefault() // evita que el blur del campo cierre esto antes del click
            onSelect(s)
          }}
        >
          {s.trigger}{s.value}
        </button>
      ))}
    </div>
  )
}