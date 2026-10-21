import { useEffect, useRef, useState } from 'react'
import styles from './EdicionModal.module.css'
import botones from '../../styles/botones.module.css'
import EdicionModal from './EdicionModal'
import CampoTextoEdicion from './CampoTextoEdicion'
import CampoVideo, { enlaceYouTubeValido } from '../Publicar/CampoVideo'
import { fetchObraDetalle, type ObraDetalle } from '../../api/suscripciones'
import { updatePost } from '../../api/postDetail'
import { useAvisoConfirmable } from '../../hooks/useAvisoConfirmable'
import { detectarReduccion } from '../../utils/avisoReduccion'
import type { FeedPost } from '../../api/feed'

interface Props {
  post: FeedPost
  onGuardado: (post: FeedPost) => void
  onCancelar: () => void
}

const NIVELES_SPOILER = [
  { valor: 'menor', etiqueta: 'Menor' },
  { valor: 'importante', etiqueta: 'Importante' },
  { valor: 'trama_central', etiqueta: 'Trama central' },
]

const ERROR_GUARDADO = 'No se pudo guardar la edición. Revisa los datos e inténtalo de nuevo.'
// Editar no consulta a la IA: si el vídeo nuevo revela más, la frontera la sube el autor.
const PISTA_VIDEO_EDICION = 'Solo YouTube. Si el vídeo revela más que el anterior, sube también la frontera.'

// jsonOError lanza el cuerpo de la respuesta: el primer mensaje de campo, si lo hay.
function mensajeEdicion(err: unknown): string {
  const detalle = (err as { detail?: unknown } | null)?.detail
  if (typeof detalle === 'string') return detalle
  if (detalle && typeof detalle === 'object') {
    const primero = Object.values(detalle)[0]
    if (Array.isArray(primero) && typeof primero[0] === 'string') return primero[0]
  }
  return ERROR_GUARDADO
}

export default function EditPostForm({ post, onGuardado, onCancelar }: Props) {
  const [detalle, setDetalle] = useState<ObraDetalle | null>(null)
  const [text, setText] = useState(post.text)
  const [referenciaId, setReferenciaId] = useState(post.referencia_narrativa?.id ?? null)
  const [fronteraId, setFronteraId] = useState<number | null>(null)
  const [nivelSpoiler, setNivelSpoiler] = useState(post.nivel_spoiler)
  const [emocionAutor, setEmocionAutor] = useState<string | null>(post.emocion_autor)
  const [imagenNueva, setImagenNueva] = useState<File | null>(null)
  const [quitarImagen, setQuitarImagen] = useState(false)
  const [preview, setPreview] = useState<string | null>(post.imagen)
  const [videoUrl, setVideoUrl] = useState('')
  const [quitarVideo, setQuitarVideo] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)
  const inputImagen = useRef<HTMLInputElement>(null)
  const aviso = useAvisoConfirmable()

  // Las galerías (2+ imágenes) aún no se editan desde aquí.
  const numGaleria = (post.imagenes ?? []).length > 1 ? (post.imagenes ?? []).length : 0
  // Post de tema sin parte: se puede seguir sin parte o anclarlo a una.
  const sinParteOriginal = post.referencia_narrativa === null
  // Vídeo e imágenes se excluyen: cada sección se oculta si la otra está en uso.
  const videoActual = post.video && !quitarVideo ? post.video : null
  const conVideo = Boolean(videoActual || videoUrl.trim())
  const conImagen = numGaleria > 0 || Boolean(preview)

  useEffect(() => {
    fetchObraDetalle(post.obra_slug).then(setDetalle)
  }, [post.obra_slug])

  // Vista previa: la nueva si se ha elegido; si no, la actual salvo que se vaya a quitar.
  useEffect(() => {
    if (!imagenNueva) {
      setPreview(quitarImagen ? null : post.imagen)
      return
    }
    const url = URL.createObjectURL(imagenNueva)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [imagenNueva, quitarImagen, post.imagen])

  function handleElegirImagen(e: React.ChangeEvent<HTMLInputElement>) {
    const archivo = e.target.files?.[0] ?? null
    if (archivo) {
      setImagenNueva(archivo)
      setQuitarImagen(false)
    }
    e.target.value = ''
  }

  function handleQuitarImagen() {
    setImagenNueva(null)
    setQuitarImagen(true)
  }

  async function handleGuardar() {
    if (!detalle) return
    setError(null)

    const bloqueado = aviso.bloquea(detectarReduccion({
      unidades: detalle.unidades,
      referenciaOriginalId: post.referencia_narrativa?.id ?? null,
      referenciaNuevaId: referenciaId,
      fronteraOriginalId: post.frontera_spoiler?.id ?? null,
      fronteraNuevaId: fronteraId,
    }))
    if (bloqueado) return

    const videoNuevo = videoUrl.trim()
    setGuardando(true)
    try {
      const actualizado = await updatePost(post.id, {
        text,
        image: imagenNueva ?? undefined,
        quitarImagen: quitarImagen && !imagenNueva,
        videoUrl: videoNuevo || undefined,
        quitarVideo: quitarVideo && !videoNuevo,
        referenciaNarrativaId: referenciaId ?? undefined,
        fronteraSpoilerId: fronteraId ?? undefined,
        nivelSpoiler,
        emocionAutor,
      })
      onGuardado(actualizado)
    } catch (err) {
      setError(mensajeEdicion(err))
    } finally {
      setGuardando(false)
    }
  }

  if (!detalle) {
    return null
  }

  return (
    <EdicionModal
      titulo="Editar publicación"
      error={error}
      aviso={aviso.aviso}
      onConfirmarAviso={aviso.confirmar}
      guardando={guardando}
      puedeGuardar={text.trim().length > 0 && enlaceYouTubeValido(videoUrl)}
      onGuardar={handleGuardar}
      onCancelar={onCancelar}
    >
      <CampoTextoEdicion
        id="edit-text"
        etiqueta="Texto"
        value={text}
        onChange={setText}
        emocion={emocionAutor}
        onEmocionChange={setEmocionAutor}
      />

      {!conVideo && (numGaleria > 0 ? (
        <div className={styles.field}>
          <span className={styles.label}>Imágenes</span>
          <p className={styles.warningBox}>
            Esta publicación tiene una galería de {numGaleria} imágenes. Por ahora no se puede editar desde aquí.
          </p>
        </div>
      ) : (
        <div className={styles.field}>
          <span className={styles.label}>Imagen (opcional)</span>
          {preview && <img className={styles.preview} src={preview} alt="" />}
          <div className={styles.imagenAcciones}>
            <button type="button" className={botones.secundario} onClick={() => inputImagen.current?.click()}>
              {preview ? 'Cambiar imagen' : 'Añadir imagen'}
            </button>
            {preview && (
              <button type="button" className={styles.confirmLink} onClick={handleQuitarImagen}>
                Quitar imagen
              </button>
            )}
            <input
              ref={inputImagen}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className={styles.inputOculto}
              onChange={handleElegirImagen}
            />
          </div>
        </div>
      ))}

      {!conImagen && (
        <div className={styles.field}>
          {videoActual && (
            <>
              <span className={styles.label}>Vídeo actual</span>
              <div className={styles.imagenAcciones}>
                <span>🎬 {videoActual.titulo}</span>
                <button type="button" className={styles.confirmLink} onClick={() => setQuitarVideo(true)}>
                  Quitar vídeo
                </button>
              </div>
            </>
          )}
          <CampoVideo
            id="edit-video"
            etiqueta={videoActual ? 'Cambiar por otro vídeo (opcional)' : 'Vídeo de YouTube (opcional)'}
            valor={videoUrl}
            onChange={setVideoUrl}
            pista={PISTA_VIDEO_EDICION}
          />
        </div>
      )}

      <div className={styles.field}>
        <label className={styles.label} htmlFor="edit-referencia">¿De qué parte habla?</label>
        <select
          id="edit-referencia"
          className={styles.select}
          value={referenciaId ?? ''}
          onChange={(e) => {
            setReferenciaId(Number(e.target.value) || null)
            aviso.reiniciar()
          }}
        >
          {sinParteOriginal && <option value="">Sin parte concreta (habla de un tema)</option>}
          {detalle.unidades.map((u) => (
            <option key={u.id} value={u.id}>{u.etiqueta}</option>
          ))}
        </select>
      </div>

      <div className={styles.field}>
        <label className={styles.label} htmlFor="edit-frontera">
          Frontera de spoiler (déjalo vacío para no cambiarla)
        </label>
        <select
          id="edit-frontera"
          className={styles.select}
          value={fronteraId ?? ''}
          onChange={(e) => {
            setFronteraId(Number(e.target.value) || null)
            aviso.reiniciar()
          }}
        >
          <option value="">No cambiar</option>
          {detalle.unidades.map((u) => (
            <option key={u.id} value={u.id}>{u.etiqueta}</option>
          ))}
        </select>
      </div>

      <div className={styles.field}>
        <label className={styles.label} htmlFor="edit-nivel">Nivel de spoiler</label>
        <select
          id="edit-nivel"
          className={styles.select}
          value={nivelSpoiler}
          onChange={(e) => setNivelSpoiler(e.target.value)}
        >
          {NIVELES_SPOILER.map((n) => (
            <option key={n.valor} value={n.valor}>{n.etiqueta}</option>
          ))}
        </select>
      </div>
    </EdicionModal>
  )
}