import { useRef, useState, type RefObject, type KeyboardEvent } from 'react'
import { fetchMentionSuggestions, fetchHashtagSuggestions } from '../api/textAutocomplete'

export interface AutocompleteSuggestion {
  trigger: '@' | '#'
  value: string
}

interface Args {
  value: string
  onChange: (value: string) => void
  fieldRef: RefObject<HTMLTextAreaElement | HTMLInputElement | null>
}

function detectarToken(texto: string, cursor: number) {
  let i = cursor - 1
  while (i >= 0 && /\w/.test(texto[i])) i--
  if (i < 0) return null
  const caracter = texto[i]
  if (caracter !== '@' && caracter !== '#') return null
  const antes = i === 0 ? '' : texto[i - 1]
  if (antes && !/\s/.test(antes)) return null
  return { inicio: i, trigger: caracter as '@' | '#', query: texto.slice(i + 1, cursor) }
}

/** Autocompletado de @menciones y #hashtags para un input o textarea
 * controlado. El desplegable se ancla bajo el campo (mismo patrón que
 * EmocionPopover), sin calcular la posición del cursor en píxeles. */
export function useMentionHashtagAutocomplete({ value, onChange, fieldRef }: Args) {
  const [suggestions, setSuggestions] = useState<AutocompleteSuggestion[]>([])
  const [activeIndex, setActiveIndex] = useState(0)
  const tokenStartRef = useRef<number | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const requestIdRef = useRef(0)

  function handleChange(nuevoValor: string) {
    onChange(nuevoValor)
    const cursor = fieldRef.current?.selectionStart ?? nuevoValor.length
    const token = detectarToken(nuevoValor, cursor)

    if (!token || token.query.length === 0) {
      setSuggestions([])
      tokenStartRef.current = null
      return
    }

    tokenStartRef.current = token.inicio
    setActiveIndex(0)

    if (debounceRef.current) clearTimeout(debounceRef.current)
    const idPeticion = ++requestIdRef.current
    debounceRef.current = setTimeout(() => {
      const buscar = token.trigger === '@' ? fetchMentionSuggestions : fetchHashtagSuggestions
      buscar(token.query).then((data) => {
        if (idPeticion !== requestIdRef.current) return // respuesta obsoleta
        const valores = token.trigger === '@'
          ? data.results.map((r) => (r as { username: string }).username)
          : data.results.map((r) => (r as { name: string }).name)
        setSuggestions(valores.map((v) => ({ trigger: token.trigger, value: v })))
      })
    }, 250)
  }

  function seleccionar(sugerencia: AutocompleteSuggestion) {
    if (tokenStartRef.current === null) return
    const cursor = fieldRef.current?.selectionStart ?? value.length
    const antes = value.slice(0, tokenStartRef.current)
    const despues = value.slice(cursor)
    const inserted = `${sugerencia.trigger}${sugerencia.value} `
    const nuevoValor = antes + inserted + despues
    onChange(nuevoValor)
    setSuggestions([])
    tokenStartRef.current = null

    requestAnimationFrame(() => {
      const pos = antes.length + inserted.length
      fieldRef.current?.setSelectionRange(pos, pos)
      fieldRef.current?.focus()
    })
  }

  function handleKeyDown(e: KeyboardEvent): boolean {
    if (suggestions.length === 0) return false
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex((i) => (i + 1) % suggestions.length)
      return true
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((i) => (i - 1 + suggestions.length) % suggestions.length)
      return true
    }
    if (e.key === 'Enter' || e.key === 'Tab') {
      e.preventDefault()
      seleccionar(suggestions[activeIndex])
      return true
    }
    if (e.key === 'Escape') {
      setSuggestions([])
      return true
    }
    return false
  }

  return {
    suggestions,
    activeIndex,
    handleChange,
    handleKeyDown,
    seleccionar,
    cerrar: () => setSuggestions([]),
  }
}