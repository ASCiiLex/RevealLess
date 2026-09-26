import { useEffect, useState } from 'react'
import styles from './NarrativaSelector.module.css'
import { fetchObraDetalle, type ObraDetalle } from '../../api/suscripciones'

export interface NarrativaValue {
  referenciaId: number | null
  fronteraId: number | null
  obraCruzadaId: number | null
  fronteraCruzadaId: number | null
}

export const NARRATIVA_VACIA: NarrativaValue = {
  referenciaId: null,
  fronteraId: null,
  obraCruzadaId: null,
  fronteraCruzadaId: null,
}

interface Props {
  obraLocal: ObraDetalle
  value: NarrativaValue
  onChange: (value: NarrativaValue) => void
}

const ESTA_OBRA = ''

export default function NarrativaSelector({ obraLocal, value, onChange }: Props) {
  const [abierto, setAbierto] = useState(false)
  const [obraCruzadaDetalle, setObraCruzadaDetalle] = useState<ObraDetalle | null>(null)

  const esCruzada = value.obraCruzadaId !== null
  const obraCruzadaActual = obraLocal.obras_relacionadas.find((o) => o.id === value.obraCruzadaId)
  const obraCruzadaSlug = obraCruzadaActual?.slug

  useEffect(() => {
    if (obraCruzadaSlug) {
      fetchObraDetalle(obraCruzadaSlug).then(setObraCruzadaDetalle)
    } else {
      setObraCruzadaDetalle(null)
    }
  }, [obraCruzadaSlug])

  const unidadesFrontera = esCruzada ? obraCruzadaDetalle?.unidades ?? [] : obraLocal.unidades
  const fronteraSeleccionada = esCruzada ? value.fronteraCruzadaId : value.fronteraId

  function handleObraChange(idStr: string) {
    onChange(
      idStr === ESTA_OBRA
        ? { ...NARRATIVA_VACIA, referenciaId: value.referenciaId }
        : { ...NARRATIVA_VACIA, obraCruzadaId: Number(idStr) }
    )
  }

  function handleReferenciaChange(idStr: string) {
    onChange({ ...value, referenciaId: Number(idStr) || null })
  }

  function handleFronteraChange(idStr: string) {
    const id = Number(idStr) || null
    onChange(esCruzada ? { ...value, fronteraCruzadaId: id } : { ...value, fronteraId: id })
  }

  const referenciaActual = obraLocal.unidades.find((u) => u.id === value.referenciaId)
  const fronteraActual = unidadesFrontera.find((u) => u.id === fronteraSeleccionada)

  const resumen = obraCruzadaActual
    ? `De: ${obraCruzadaActual.titulo}${fronteraActual ? ` · ${fronteraActual.etiqueta}` : ''}`
    : referenciaActual
      ? `De: ${referenciaActual.etiqueta}`
      : '¿De qué parte trata el comentario? (opcional)'

  return (
    <div className={styles.wrapper}>
      <button
        type="button"
        className={styles.toggle}
        onClick={() => setAbierto((v) => !v)}
        aria-expanded={abierto}
      >
        <span className={styles.toggleText}>{resumen}</span>
        <span className={styles.chevron} aria-hidden="true">{abierto ? '▾' : '▸'}</span>
      </button>

      {abierto && (
        <div className={styles.row}>
          {obraLocal.obras_relacionadas.length > 0 && (
            <select
              className={styles.select}
              value={value.obraCruzadaId ?? ESTA_OBRA}
              onChange={(e) => handleObraChange(e.target.value)}
              aria-label="Obra"
            >
              <option value={ESTA_OBRA}>Esta obra</option>
              {obraLocal.obras_relacionadas.map((o) => (
                <option key={o.id} value={o.id}>{o.titulo}</option>
              ))}
            </select>
          )}

          <select
            className={styles.select}
            value={value.referenciaId ?? ''}
            onChange={(e) => handleReferenciaChange(e.target.value)}
            disabled={esCruzada}
            aria-label="Referencia narrativa"
          >
            <option value="">{esCruzada ? '—' : 'Referencia'}</option>
            {obraLocal.unidades.map((u) => (
              <option key={u.id} value={u.id}>{u.etiqueta}</option>
            ))}
          </select>

          <select
            className={styles.select}
            value={fronteraSeleccionada ?? ''}
            onChange={(e) => handleFronteraChange(e.target.value)}
            disabled={esCruzada && !obraCruzadaDetalle}
            aria-label="Frontera de spoiler"
          >
            <option value="">Frontera</option>
            {unidadesFrontera.map((u) => (
              <option key={u.id} value={u.id}>{u.etiqueta}</option>
            ))}
          </select>
        </div>
      )}
    </div>
  )
}