import { useEffect, useRef, useState, type FormEvent } from 'react'
import styles from './PasoPost.module.css'
import BuscadorLocal, { type BuscadorItem } from './BuscadorLocal'
import { fetchObraDetalle, type ObraDetalle } from '../../api/suscripciones'
import { crearPost } from '../../api/publicar'
import type { DeteccionCruzada } from '../../api/publicar'
import { fetchSuggestedHashtags } from '../../api/textAutocomplete'
import { useMentionHashtagAutocomplete } from '../../hooks/useMentionHashtagAutocomplete'
import AutocompleteDropdown from '../Autocomplete/AutocompleteDropdown'
import EmocionPopover from '../Emociones/EmocionPopover'
import { EMOCIONES } from '../../constants/emociones'
import ReferenciaCruzadaAviso from '../ReferenciaCruzada/ReferenciaCruzadaAviso'

interface Props {
  obraSlug: string
  obraTitulo: string
  temaIdInicial?: number | null
  onPublicado: (postId: number) => void
  onProgresoRequerido: () => void
}

export default function PasoPost({ obraSlug, obraTitulo, temaIdInicial, onPublicado, onProgresoRequerido }: Props) {
  const [detalle, setDetalle] = useState<ObraDetalle | null>(null)
  const [text, setText] = useState('')
  const [image, setImage] = useState<File | null>(null)
  const [referenciaId, setReferenciaId] = useState<number | null>(null)
  const [fronteraId, setFronteraId] = useState<number | null>(null)
  const [emocionAutor, setEmocionAutor] = useState<string | null>(null)
  const [emocionAbierta, setEmocionAbierta] = useState(false)
  const [temaId, setTemaId] = useState<number | null>(temaIdInicial ?? null)
  const [nuevoProgresoId, setNuevoProgresoId] = useState<number | null>(null)
  const [confirmarSalto, setConfirmarSalto] = useState(false)
  const [avisoSalto, setAvisoSalto] = useState<string | null>(null)
  const [detecciones, setDetecciones] = useState<DeteccionCruzada[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [hashtagsSugeridos, setHashtagsSugeridos] = useState<string[]>([])

  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const autocomplete = useMentionHashtagAutocomplete({ value: text, onChange: setText, fieldRef: textareaRef })

  useEffect(() => {
    fetchObraDetalle(obraSlug).then(setDetalle)
    fetchSuggestedHashtags().then((data) => setHashtagsSugeridos(data.results))
  }, [obraSlug])

  function insertarHashtagSugerido(tag: string) {
    const campo = textareaRef.current
    const inserted = `#${tag} `
    const cursor = campo?.selectionStart ?? text.length
    const nuevoValor = text.slice(0, cursor) + inserted + text.slice(cursor)
    setText(nuevoValor)
    requestAnimationFrame(() => {
      const pos = cursor + inserted.length
      campo?.setSelectionRange(pos, pos)
      campo?.focus()
    })
  }

  async function enviar(overrides: {
    obraCruzadaId?: number | null
    fronteraCruzadaId?: number | null
    descartarReferenciaCruzada?: boolean
  } = {}) {
    if (!referenciaId) return
    setError(null)
    setAvisoSalto(null)
    setEnviando(true)

    try {
      const resultado = await crearPost(obraSlug, {
        text,
        image,
        referenciaNarrativaId: referenciaId,
        fronteraSpoilerId: fronteraId,
        emocionAutor,
        temaId,
        nuevoProgresoId,
        confirmarSaltoProgreso: confirmarSalto,
        ...overrides,
      })

      if ('progresoRequerido' in resultado) {
        onProgresoRequerido()
        return
      }
      if ('requiereConfirmacion' in resultado) {
        setAvisoSalto(resultado.detail)
        return
      }
      if ('referenciaCruzadaDetectada' in resultado) {
        setDetecciones(resultado.detecciones)
        return
      }

      setDetecciones(null)
      onPublicado(resultado.id)
    } catch {
      setError('No se pudo publicar. Revisa los datos e inténtalo de nuevo.')
    } finally {
      setEnviando(false)
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    enviar()
  }

  if (!detalle) {
    return null
  }

  const unidadesItems: BuscadorItem[] = detalle.unidades.map((u) => ({ id: u.id, label: u.etiqueta }))
  const temasItems: BuscadorItem[] = detalle.temas.map((t) => ({ id: t.id, label: t.nombre }))
  const emocionActual = EMOCIONES.find((e) => e.clave === emocionAutor)

  return (
    <div className={styles.wrapper}>
      <h1 className={styles.title}>Publicar · {obraTitulo}</h1>

      <form className={styles.form} onSubmit={handleSubmit}>
        {error && <p className={styles.error}>{error}</p>}
        {avisoSalto && (
          <p className={styles.error}>
            {avisoSalto}{' '}
            <button type="button" onClick={() => { setConfirmarSalto(true); enviar() }}>
              Confirmar y publicar
            </button>
          </p>
        )}

        <div className={styles.field}>
          <label className={styles.label} htmlFor="referencia">¿De qué parte habla?</label>
          <BuscadorLocal
            id="referencia"
            items={unidadesItems}
            value={referenciaId}
            onChange={setReferenciaId}
            placeholder="Elige una unidad"
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="tema">Tema transversal (opcional)</label>
          <BuscadorLocal
            id="tema"
            items={temasItems}
            value={temaId}
            onChange={setTemaId}
            placeholder="Buscar tema..."
            emptyLabel="Ninguno"
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="text">¿Qué quieres contar?</label>
          <div className={styles.postBox}>
            <div className={styles.textareaWrap}>
              <textarea
                id="text"
                ref={textareaRef}
                className={styles.textarea}
                value={text}
                onChange={(e) => autocomplete.handleChange(e.target.value)}
                onKeyDown={autocomplete.handleKeyDown}
                onFocus={() => setEmocionAbierta(true)}
                onBlur={() => setTimeout(() => { autocomplete.cerrar(); setEmocionAbierta(false) }, 150)}
                required
              />
              <AutocompleteDropdown
                suggestions={autocomplete.suggestions}
                activeIndex={autocomplete.activeIndex}
                onSelect={autocomplete.seleccionar}
              />
              <EmocionPopover visible={emocionAbierta} value={emocionAutor} onSelect={setEmocionAutor} />
            </div>

            {hashtagsSugeridos.length > 0 && (
              <div className={styles.hashtagsSugeridos}>
                {hashtagsSugeridos.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    className={styles.hashtagChip}
                    onClick={() => insertarHashtagSugerido(tag)}
                  >
                    #{tag}
                  </button>
                ))}
              </div>
            )}

            <div className={styles.postBoxFooter}>
              {emocionActual && (
                <span className={styles.emocionElegida}>
                  {emocionActual.emoji} {emocionActual.etiqueta}
                  <button type="button" className={styles.emocionQuitar} onClick={() => setEmocionAutor(null)}>×</button>
                </span>
              )}
              <button
                type="button"
                className={styles.imageButton}
                onClick={() => fileInputRef.current?.click()}
              >
                {image ? image.name : '📷 Añadir imagen'}
              </button>
              <input
                ref={fileInputRef}
                className={styles.imageInputHidden}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={(e) => setImage(e.target.files?.[0] ?? null)}
              />
            </div>
          </div>
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="nuevo-progreso">
            Actualizar mi progreso a (opcional)
          </label>
          <BuscadorLocal
            id="nuevo-progreso"
            items={unidadesItems}
            value={nuevoProgresoId}
            onChange={setNuevoProgresoId}
            placeholder="Buscar unidad..."
            emptyLabel="No actualizar"
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="frontera">
            Frontera de spoiler (opcional)
          </label>
          <BuscadorLocal
            id="frontera"
            items={unidadesItems}
            value={fronteraId}
            onChange={setFronteraId}
            placeholder="Buscar unidad..."
            emptyLabel="Dejar que la IA sugiera (o usar tu progreso actual)"
          />
          <span className={styles.hint}>
            Si no se indica, se intenta clasificar automáticamente; si no es posible, se usa tu progreso actual.
          </span>
        </div>

        <button className={styles.submit} type="submit" disabled={enviando || !referenciaId}>
          {enviando ? 'Publicando...' : 'Publicar'}
        </button>
      </form>

      {detecciones && (
        <ReferenciaCruzadaAviso
          detecciones={detecciones}
          onConfirmar={(obraCruzadaId, fronteraCruzadaId) => {
            setDetecciones(null)
            enviar({ obraCruzadaId, fronteraCruzadaId })
          }}
          onDescartar={() => {
            setDetecciones(null)
            enviar({ descartarReferenciaCruzada: true })
          }}
          onCancelar={() => setDetecciones(null)}
        />
      )}
    </div>
  )
}