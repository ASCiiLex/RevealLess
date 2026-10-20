import { useEffect, useState, type FormEvent } from 'react'
import { createPortal } from 'react-dom'
import styles from './SugerirObra.module.css'
import { ApiError } from '../../api/client'
import { TIPOS_OBRA, crearSolicitudObra, type TipoObra } from '../../api/solicitudesObra'

interface Props {
  tituloInicial?: string
  onClose: () => void
}

const ERROR_GENERICO = 'No se pudo enviar la sugerencia. Inténtalo de nuevo más tarde.'

function mensajeDeError(err: unknown): string {
  const cuerpo = err instanceof ApiError ? (err.detail as Record<string, unknown> | null) : null
  const detalle = cuerpo?.detail ?? (cuerpo ? Object.values(cuerpo)[0] : null)
  if (typeof detalle === 'string') return detalle
  if (Array.isArray(detalle) && typeof detalle[0] === 'string') return detalle[0]
  return ERROR_GENERICO
}

// En un portal: así no lo cierran los clics fuera del buscador que lo abre.
export default function SugerirObraModal({ tituloInicial = '', onClose }: Props) {
  const [titulo, setTitulo] = useState(tituloInicial)
  const [tipo, setTipo] = useState<TipoObra>('serie')
  const [enlace, setEnlace] = useState('')
  const [comentario, setComentario] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [enviada, setEnviada] = useState(false)

  useEffect(() => {
    function alPulsar(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', alPulsar)
    return () => document.removeEventListener('keydown', alPulsar)
  }, [onClose])

  async function enviar(e: FormEvent) {
    e.preventDefault()
    if (!titulo.trim() || enviando) return
    setEnviando(true)
    setError(null)
    try {
      await crearSolicitudObra({ titulo: titulo.trim(), tipo, enlace: enlace.trim(), comentario: comentario.trim() })
      setEnviada(true)
    } catch (err) {
      setError(mensajeDeError(err))
    } finally {
      setEnviando(false)
    }
  }

  return createPortal(
    <div className={styles.fondo} onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={styles.modal} role="dialog" aria-modal="true" aria-labelledby="sugerir-obra-titulo">
        <h2 id="sugerir-obra-titulo" className={styles.titulo}>Sugerir una obra</h2>

        {enviada ? (
          <>
            <p className={styles.texto}>
              ¡Gracias! La revisaremos y te avisaremos en cuanto la añadamos al catálogo.
            </p>
            <div className={styles.acciones}>
              <button type="button" className={styles.principal} onClick={onClose}>Cerrar</button>
            </div>
          </>
        ) : (
          <form onSubmit={enviar}>
            <label className={styles.campo}>
              <span className={styles.etiqueta}>Título</span>
              <input
                className={styles.entrada}
                value={titulo}
                onChange={(e) => setTitulo(e.target.value)}
                maxLength={200}
                required
                autoFocus
              />
            </label>

            <label className={styles.campo}>
              <span className={styles.etiqueta}>Tipo</span>
              <select className={styles.entrada} value={tipo} onChange={(e) => setTipo(e.target.value as TipoObra)}>
                {TIPOS_OBRA.map((t) => (
                  <option key={t.valor} value={t.valor}>{t.etiqueta}</option>
                ))}
              </select>
            </label>

            <label className={styles.campo}>
              <span className={styles.etiqueta}>Enlace de referencia (opcional)</span>
              <input
                className={styles.entrada}
                type="url"
                placeholder="Ficha en MyAnimeList, IMDb, Goodreads…"
                value={enlace}
                onChange={(e) => setEnlace(e.target.value)}
              />
            </label>

            <label className={styles.campo}>
              <span className={styles.etiqueta}>Comentario (opcional)</span>
              <textarea
                className={styles.entrada}
                rows={3}
                maxLength={300}
                value={comentario}
                onChange={(e) => setComentario(e.target.value)}
              />
            </label>

            {error && <p className={styles.error}>{error}</p>}

            <div className={styles.acciones}>
              <button type="button" className={styles.secundario} onClick={onClose}>Cancelar</button>
              <button type="submit" className={styles.principal} disabled={enviando || !titulo.trim()}>
                {enviando ? 'Enviando…' : 'Enviar sugerencia'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>,
    document.body,
  )
}