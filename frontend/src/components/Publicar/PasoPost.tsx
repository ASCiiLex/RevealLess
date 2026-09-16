import { useEffect, useState, type FormEvent } from 'react'
import styles from './PasoPost.module.css'
import { fetchObraDetalle, type ObraDetalle } from '../../api/suscripciones'
import { crearPost } from '../../api/publicar'
import EmocionSelector from '../Emociones/EmocionSelector'

interface Props {
  obraSlug: string
  obraTitulo: string
  onPublicado: (postId: number) => void
  onProgresoRequerido: () => void
}

export default function PasoPost({ obraSlug, obraTitulo, onPublicado, onProgresoRequerido }: Props) {
  const [detalle, setDetalle] = useState<ObraDetalle | null>(null)
  const [text, setText] = useState('')
  const [image, setImage] = useState<File | null>(null)
  const [referenciaId, setReferenciaId] = useState<number | null>(null)
  const [fronteraId, setFronteraId] = useState<number | null>(null)
  const [emocionAutor, setEmocionAutor] = useState<string | null>(null)
  const [nuevoProgresoId, setNuevoProgresoId] = useState<number | null>(null)
  const [confirmarSalto, setConfirmarSalto] = useState(false)
  const [avisoSalto, setAvisoSalto] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    fetchObraDetalle(obraSlug).then(setDetalle)
  }, [obraSlug])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
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
        nuevoProgresoId,
        confirmarSaltoProgreso: confirmarSalto,
      })

      if ('progresoRequerido' in resultado) {
        // El backend es la única fuente de verdad real sobre si hace
        // falta progreso -- la heurística optimista de PublicarFlow
        // (saltar directo a este paso) puede equivocarse, y aquí es
        // donde se corrige devolviendo al paso de declarar progreso.
        onProgresoRequerido()
        return
      }
      if ('requiereConfirmacion' in resultado) {
        setAvisoSalto(resultado.detail)
        return
      }

      onPublicado(resultado.id)
    } catch {
      setError('No se pudo publicar. Revisa los datos e inténtalo de nuevo.')
    } finally {
      setEnviando(false)
    }
  }

  if (!detalle) {
    return null
  }

  return (
    <div className={styles.wrapper}>
      <h1 className={styles.title}>Publicar · {obraTitulo}</h1>

      <form className={styles.form} onSubmit={handleSubmit}>
        {error && <p className={styles.error}>{error}</p>}
        {avisoSalto && (
          <p className={styles.error}>
            {avisoSalto}{' '}
            <button type="button" onClick={() => setConfirmarSalto(true)}>
              Confirmar y publicar
            </button>
          </p>
        )}

        <div className={styles.field}>
          <label className={styles.label} htmlFor="text">¿Qué estás pensando?</label>
          <textarea
            id="text"
            className={styles.textarea}
            value={text}
            onChange={(e) => setText(e.target.value)}
            required
          />
        </div>

        <EmocionSelector value={emocionAutor} onChange={setEmocionAutor} />

        <div className={styles.field}>
          <label className={styles.label} htmlFor="image">Imagen (opcional)</label>
          <input
            id="image"
            className={styles.input}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => setImage(e.target.files?.[0] ?? null)}
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="referencia">¿De qué parte habla?</label>
          <select
            id="referencia"
            className={styles.select}
            value={referenciaId ?? ''}
            onChange={(e) => setReferenciaId(Number(e.target.value) || null)}
            required
          >
            <option value="">Elige una unidad</option>
            {detalle.unidades.map((u) => (
              <option key={u.id} value={u.id}>{u.etiqueta}</option>
            ))}
          </select>
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="frontera">
            Frontera de spoiler (opcional)
          </label>
          <select
            id="frontera"
            className={styles.select}
            value={fronteraId ?? ''}
            onChange={(e) => setFronteraId(Number(e.target.value) || null)}
          >
            <option value="">Dejar que la IA sugiera (o usar tu progreso actual)</option>
            {detalle.unidades.map((u) => (
              <option key={u.id} value={u.id}>{u.etiqueta}</option>
            ))}
          </select>
          <span className={styles.hint}>
            Si no se indica, se intenta clasificar automáticamente; si no es posible, se usa tu progreso actual.
          </span>
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="nuevo-progreso">
            Actualizar mi progreso a (opcional)
          </label>
          <select
            id="nuevo-progreso"
            className={styles.select}
            value={nuevoProgresoId ?? ''}
            onChange={(e) => setNuevoProgresoId(Number(e.target.value) || null)}
          >
            <option value="">No actualizar</option>
            {detalle.unidades.map((u) => (
              <option key={u.id} value={u.id}>{u.etiqueta}</option>
            ))}
          </select>
        </div>

        <button className={styles.submit} type="submit" disabled={enviando || !referenciaId}>
          {enviando ? 'Publicando...' : 'Publicar'}
        </button>
      </form>
    </div>
  )
}