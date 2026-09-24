import { useEffect, useState } from 'react'
import styles from './ReferenciaCruzadaAviso.module.css'
import { fetchObraDetalle } from '../../api/suscripciones'

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
  onConfirmar: (obraCruzadaId: number, fronteraCruzadaId: number) => void
  onDescartar: () => void
  onCancelar: () => void
}

export default function ReferenciaCruzadaAviso({ detecciones, onConfirmar, onDescartar, onCancelar }: Props) {
  const [obraId, setObraId] = useState(detecciones[0]?.obraId ?? null)
  const [unidades, setUnidades] = useState<UnidadOpcion[]>([])
  const [fronteraId, setFronteraId] = useState<number | null>(null)

  const detectada = detecciones.find((d) => d.obraId === obraId) ?? detecciones[0]

  useEffect(() => {
    if (detectada) {
      fetchObraDetalle(detectada.obraSlug).then((d) => setUnidades(d.unidades))
    }
  }, [detectada?.obraSlug])

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
          onChange={(e) => setFronteraId(Number(e.target.value) || null)}
        >
          <option value="">Elige el punto de {detectada.obraTitulo}</option>
          {unidades.map((u) => (
            <option key={u.id} value={u.id}>{u.etiqueta}</option>
          ))}
        </select>

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