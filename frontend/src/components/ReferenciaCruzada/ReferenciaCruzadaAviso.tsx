import { useEffect, useState } from 'react'
import styles from './ReferenciaCruzadaAviso.module.css'
import { fetchObraDetalle } from '../../api/suscripciones'
import { normalizar } from '../../utils/texto'

export interface DeteccionCruzada {
  obraId: number
  obraTitulo: string
  obraSlug: string
  palabra: string
}

interface UnidadOpcion {
  id: number
  etiqueta: string
}

interface Props {
  detecciones: DeteccionCruzada[]
  // Parte elegida en la obra principal: si la otra obra tiene una con el mismo nombre, se propone.
  parteNombre?: string | null
  onConfirmar: (obraCruzadaId: number, fronteraCruzadaId: number) => void
  onDescartar: () => void
  onCancelar: () => void
}

// «Saga · Arco» → «Arco»: se compara el nombre propio de la unidad.
const nombreBase = (nombre: string) => nombre.split(' · ').pop() ?? nombre

export default function ReferenciaCruzadaAviso({ detecciones, parteNombre, onConfirmar, onDescartar, onCancelar }: Props) {
  const [obraId, setObraId] = useState(detecciones[0]?.obraId ?? null)
  const [unidades, setUnidades] = useState<UnidadOpcion[]>([])
  const [fronteraId, setFronteraId] = useState<number | null>(null)
  const [propuesta, setPropuesta] = useState(false)

  const detectada = detecciones.find((d) => d.obraId === obraId) ?? detecciones[0]

  useEffect(() => {
    if (!detectada) return
    let vigente = true
    fetchObraDetalle(detectada.obraSlug).then((d) => {
      if (!vigente) return
      setUnidades(d.unidades)
      const buscado = parteNombre ? normalizar(nombreBase(parteNombre)) : null
      const igual = buscado ? d.unidades.find((u) => normalizar(u.etiqueta) === buscado) : undefined
      setFronteraId(igual?.id ?? null)
      setPropuesta(Boolean(igual))
    })
    return () => {
      vigente = false
    }
  }, [detectada?.obraSlug, parteNombre])

  if (!detectada) {
    return null
  }

  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        <h3 className={styles.title}>Posible referencia a otra obra</h3>
        <p className={styles.text}>
          El texto contiene la palabra "<strong>{detectada.palabra}</strong>", que podría
          referirse a <strong>{detectada.obraTitulo}</strong>. Si es así, indica hasta qué
          punto de esa obra hay que haber llegado para leer esto sin spoiler.
        </p>

        {detecciones.length > 1 && (
          <select
            className={styles.select}
            value={obraId ?? ''}
            onChange={(e) => {
              setObraId(Number(e.target.value))
              setFronteraId(null)
            }}
          >
            {detecciones.map((d) => (
              <option key={d.obraId} value={d.obraId}>{d.obraTitulo}</option>
            ))}
          </select>
        )}

        <select
          className={styles.select}
          value={fronteraId ?? ''}
          onChange={(e) => {
            setFronteraId(Number(e.target.value) || null)
            setPropuesta(false)
          }}
        >
          <option value="">Elige el punto de {detectada.obraTitulo}</option>
          {unidades.map((u) => (
            <option key={u.id} value={u.id}>{u.etiqueta}</option>
          ))}
        </select>

        {propuesta && (
          <p className={styles.text}>
            Propuesta: la parte con el mismo nombre en {detectada.obraTitulo}. Cámbiala si no coincide.
          </p>
        )}

        <div className={styles.actions}>
          <button
            className={styles.confirmar}
            disabled={!fronteraId}
            onClick={() => fronteraId && onConfirmar(detectada.obraId, fronteraId)}
          >
            Sí, es de ahí — confirmar
          </button>
          <button className={styles.descartar} onClick={onDescartar}>
            No, es coincidencia — publicar igual
          </button>
          <button className={styles.cancelar} onClick={onCancelar}>
            Cancelar
          </button>
        </div>
      </div>
    </div>
  )
}