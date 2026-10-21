import { useEffect, useRef, useState } from 'react'
import styles from './ReproductorVideo.module.css'
import type { VideoPost } from '../../api/feed'

interface Props {
  video: VideoPost
}

// Lo mínimo de la API del reproductor de YouTube que se usa aquí.
interface ReproductorYT {
  playVideo(): void
  destroy(): void
}

declare global {
  interface Window {
    YT?: { Player: new (elemento: HTMLElement, opciones: Record<string, unknown>) => ReproductorYT }
    onYouTubeIframeAPIReady?: () => void
  }
}

type Estado = 'portada' | 'cargando' | 'activo' | 'pausado' | 'error'

const TERMINADO = 0
const REPRODUCIENDO = 1
const PAUSADO = 2
// Medidas de referencia 16:9: reservan el hueco antes de cargar la portada.
const ANCHO = 900
const ALTO = 506

let cargaApi: Promise<void> | null = null

// El script de YouTube solo se pide al pulsar «play» por primera vez.
function cargarApiYouTube(): Promise<void> {
  if (window.YT?.Player) return Promise.resolve()
  if (!cargaApi) {
    cargaApi = new Promise((resolve, reject) => {
      const anterior = window.onYouTubeIframeAPIReady
      window.onYouTubeIframeAPIReady = () => {
        anterior?.()
        resolve()
      }
      const script = document.createElement('script')
      script.src = 'https://www.youtube.com/iframe_api'
      script.async = true
      script.onerror = () => {
        cargaApi = null
        reject(new Error('No se pudo cargar YouTube'))
      }
      document.head.appendChild(script)
    })
  }
  return cargaApi
}

// Protección antispoiler: sin nada de YouTube antes de «play», sin sugerencias de otros canales,
// sin anotaciones ni pantalla completa; la pausa la tapa una capa propia y al terminar vuelve la portada.
export default function ReproductorVideo({ video }: Props) {
  const [estado, setEstado] = useState<Estado>('portada')
  const lienzo = useRef<HTMLDivElement>(null)
  const reproductor = useRef<ReproductorYT | null>(null)

  useEffect(() => () => reproductor.current?.destroy(), [])

  function volverAPortada() {
    reproductor.current?.destroy()
    reproductor.current = null
    if (lienzo.current) lienzo.current.innerHTML = ''
    setEstado('portada')
  }

  async function reproducir() {
    setEstado('cargando')
    try {
      await cargarApiYouTube()
    } catch {
      setEstado('error')
      return
    }
    if (!lienzo.current || !window.YT) return
    // YouTube sustituye el nodo que recibe: se le da uno propio, fuera del control de React.
    const destino = document.createElement('div')
    lienzo.current.appendChild(destino)
    reproductor.current = new window.YT.Player(destino, {
      host: 'https://www.youtube-nocookie.com',
      videoId: video.id,
      width: '100%',
      height: '100%',
      playerVars: { autoplay: 1, rel: 0, iv_load_policy: 3, fs: 0, playsinline: 1, modestbranding: 1 },
      events: {
        onReady: () => {
          setEstado('activo')
          reproductor.current?.playVideo()
        },
        onStateChange: (evento: { data: number }) => {
          if (evento.data === TERMINADO) volverAPortada()
          else if (evento.data === PAUSADO) setEstado('pausado')
          else if (evento.data === REPRODUCIENDO) setEstado('activo')
        },
      },
    })
  }

  const conPortada = estado === 'portada' || estado === 'cargando' || estado === 'error'
  const imagenPortada = video.portada && (
    <img className={styles.portada} src={video.portada} alt="" width={ANCHO} height={ALTO} loading="lazy" decoding="async" />
  )

  return (
    <figure className={styles.video}>
      <div className={styles.lienzo}>
        <div ref={lienzo} className={styles.marco} />

        {conPortada && (
          <button
            type="button"
            className={styles.capa}
            onClick={reproducir}
            disabled={estado === 'cargando'}
            aria-label={`Reproducir vídeo: ${video.titulo}`}
          >
            {imagenPortada}
            <span className={styles.boton} aria-hidden="true">{estado === 'cargando' ? '…' : '▶'}</span>
            {estado === 'error' && <span className={styles.aviso}>No se pudo cargar el vídeo. Pulsa para reintentar.</span>}
          </button>
        )}

        {estado === 'pausado' && (
          // Tapa lo que YouTube muestra en pausa (sugerencias de otros vídeos).
          <button
            type="button"
            className={styles.capa}
            onClick={() => reproductor.current?.playVideo()}
            aria-label="Continuar el vídeo"
          >
            {imagenPortada}
            <span className={styles.boton} aria-hidden="true">▶</span>
            <span className={styles.aviso}>Continuar</span>
          </button>
        )}
      </div>

      <figcaption className={styles.pie}>
        <span className={styles.titulo}>{video.titulo}</span>
        {video.canal && <span className={styles.canal}>{video.canal} · YouTube</span>}
      </figcaption>
    </figure>
  )
}