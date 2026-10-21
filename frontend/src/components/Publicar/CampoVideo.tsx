import styles from './CampoVideo.module.css'

interface Props {
  id: string
  etiqueta?: string
  valor: string
  onChange: (valor: string) => void
  deshabilitado?: boolean
  pista?: string
}

// Comprobación rápida en el cliente; la validación real la hace el servidor consultando YouTube.
const PATRON_YOUTUBE = /^(https?:\/\/)?(www\.|m\.)?(youtube\.com|youtu\.be|youtube-nocookie\.com)\/\S+$/i

export function enlaceYouTubeValido(valor: string): boolean {
  const limpio = valor.trim()
  return !limpio || PATRON_YOUTUBE.test(limpio)
}

const PISTA_POR_DEFECTO = 'Solo YouTube. Su título también se tiene en cuenta para la frontera de spoiler.'

export default function CampoVideo({
  id, etiqueta = 'Vídeo de YouTube (opcional)', valor, onChange, deshabilitado = false, pista,
}: Props) {
  const invalido = !enlaceYouTubeValido(valor)

  return (
    <div className={styles.campo}>
      <label className={styles.etiqueta} htmlFor={id}>{etiqueta}</label>
      <input
        id={id}
        name="video_url"
        className={styles.entrada}
        type="url"
        inputMode="url"
        placeholder="https://www.youtube.com/watch?v=…"
        value={valor}
        onChange={(e) => onChange(e.target.value)}
        disabled={deshabilitado}
        aria-invalid={invalido}
      />
      {invalido
        ? <span className={styles.error}>Ese enlace no es de YouTube.</span>
        : <span className={styles.pista}>{pista ?? PISTA_POR_DEFECTO}</span>}
    </div>
  )
}