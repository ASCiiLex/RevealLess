import { useEffect, useState } from 'react'
import styles from './OnboardingSearch.module.css'
import { buscar, type ResultadoBusqueda, type TemaBusqueda } from '../../api/buscar'
import { crearSuscripcion, eliminarSuscripcion } from '../../api/suscripciones'
import type { LomoObra } from '../Carousel/Lomo'

interface Props {
  onCambioContador: (total: number) => void
}

export default function OnboardingSearch({ onCambioContador }: Props) {
  const [query, setQuery] = useState('')
  const [resultado, setResultado] = useState<ResultadoBusqueda | null>(null)
  const [seguidos, setSeguidos] = useState<Set<string>>(new Set())

  useEffect(() => {
    if (query.trim().length < 2) {
      setResultado(null)
      return
    }
    const id = setTimeout(() => {
      buscar(query.trim()).then(setResultado)
    }, 300)
    return () => clearTimeout(id)
  }, [query])

  function marcarSeguido(clave: string, seguido: boolean) {
    setSeguidos((prev) => {
      const nuevo = new Set(prev)
      if (seguido) nuevo.add(clave)
      else nuevo.delete(clave)
      onCambioContador(nuevo.size)
      return nuevo
    })
  }

  return (
    <div>
      <input
        className={styles.searchInput}
        type="text"
        placeholder="Busca obras o temas que te interesen..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      {resultado && (
        <div className={styles.results}>
          {resultado.obras.length === 0 && resultado.temas.length === 0 ? (
            <p className={styles.empty}>Sin resultados.</p>
          ) : (
            <>
              {resultado.obras.map((obra) => (
                <ObraRow
                  key={`obra-${obra.id}`}
                  obra={obra}
                  seguido={seguidos.has(`obra-${obra.id}`)}
                  onCambio={(seguido) => marcarSeguido(`obra-${obra.id}`, seguido)}
                />
              ))}
              {resultado.temas.map((tema) => (
                <TemaRow
                  key={`tema-${tema.id}`}
                  tema={tema}
                  seguido={seguidos.has(`tema-${tema.id}`)}
                  onCambio={(seguido) => marcarSeguido(`tema-${tema.id}`, seguido)}
                />
              ))}
            </>
          )}
        </div>
      )}

      <p className={styles.contador}>
        {seguidos.size === 0
          ? 'Aún no sigues nada — puedes continuar igualmente.'
          : `Siguiendo ${seguidos.size} elemento${seguidos.size === 1 ? '' : 's'}.`}
      </p>
    </div>
  )
}

function ObraRow({
  obra,
  seguido,
  onCambio,
}: {
  obra: LomoObra
  seguido: boolean
  onCambio: (seguido: boolean) => void
}) {
  const [suscripcionId, setSuscripcionId] = useState<number | null>(null)
  const [cargando, setCargando] = useState(false)

  async function handleToggle() {
    if (cargando) return
    setCargando(true)
    try {
      if (seguido) {
        if (suscripcionId !== null) await eliminarSuscripcion(suscripcionId)
        onCambio(false)
      } else {
        const suscripcion = await crearSuscripcion(obra.slug)
        setSuscripcionId(suscripcion.id)
        onCambio(true)
      }
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className={styles.row}>
      <div className={styles.rowMain}>
        <img className={styles.thumb} src={obra.imagen_url} alt="" />
        <span className={styles.titulo}>{obra.titulo}</span>
      </div>
      <button
        className={`${styles.followButton} ${seguido ? styles.followButtonActive : ''}`}
        onClick={handleToggle}
        disabled={cargando}
      >
        {seguido ? 'Siguiendo' : 'Seguir'}
      </button>
    </div>
  )
}

function TemaRow({
  tema,
  seguido,
  onCambio,
}: {
  tema: TemaBusqueda
  seguido: boolean
  onCambio: (seguido: boolean) => void
}) {
  const [suscripcionId, setSuscripcionId] = useState<number | null>(null)
  const [cargando, setCargando] = useState(false)

  async function handleToggle() {
    if (cargando) return
    setCargando(true)
    try {
      if (seguido) {
        if (suscripcionId !== null) await eliminarSuscripcion(suscripcionId)
        onCambio(false)
      } else {
        const suscripcion = await crearSuscripcion(tema.obra_slug, { temaId: tema.id })
        setSuscripcionId(suscripcion.id)
        onCambio(true)
      }
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className={styles.row}>
      <div className={styles.rowMain}>
        <div>
          <div className={styles.titulo}>{tema.nombre}</div>
          <div className={styles.subtitulo}>{tema.obra_titulo}</div>
        </div>
      </div>
      <button
        className={`${styles.followButton} ${seguido ? styles.followButtonActive : ''}`}
        onClick={handleToggle}
        disabled={cargando}
      >
        {seguido ? 'Siguiendo' : 'Seguir'}
      </button>
    </div>
  )
}