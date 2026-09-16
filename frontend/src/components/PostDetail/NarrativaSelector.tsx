import { useState } from 'react'
import styles from './NarrativaSelector.module.css'
import type { ObraDetalle } from '../../api/suscripciones'

interface Props {
  detalle: ObraDetalle
  referenciaId: number | null
  fronteraId: number | null
  onChangeReferencia: (id: number | null) => void
  onChangeFrontera: (id: number | null) => void
}

export default function NarrativaSelector({
  detalle,
  referenciaId,
  fronteraId,
  onChangeReferencia,
  onChangeFrontera,
}: Props) {
  const [abierto, setAbierto] = useState(false)

  const referenciaActual = detalle.unidades.find((u) => u.id === referenciaId)

  return (
    <div className={styles.wrapper}>
      <button
        type="button"
        className={styles.toggle}
        onClick={() => setAbierto((v) => !v)}
        aria-expanded={abierto}
      >
        <span>
          {referenciaActual ? `De: ${referenciaActual.etiqueta}` : '¿De qué parte trata el comentario? (opcional)'}
        </span>
        <span className={styles.chevron} aria-hidden="true">{abierto ? '▾' : '▸'}</span>
      </button>

      {abierto && (
        <>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="narrativa-referencia">
              ¿De qué parte trata el comentario? (opcional)
            </label>
            <select
              id="narrativa-referencia"
              className={styles.select}
              value={referenciaId ?? ''}
              onChange={(e) => onChangeReferencia(Number(e.target.value) || null)}
            >
              <option value="">Heredar del post</option>
              {detalle.unidades.map((u) => (
                <option key={u.id} value={u.id}>{u.etiqueta}</option>
              ))}
            </select>
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="narrativa-frontera">
              ¿Hasta dónde hay que haber visto/leído? (opcional)
            </label>
            <select
              id="narrativa-frontera"
              className={styles.select}
              value={fronteraId ?? ''}
              onChange={(e) => onChangeFrontera(Number(e.target.value) || null)}
            >
              <option value="">Heredar del post</option>
              {detalle.unidades.map((u) => (
                <option key={u.id} value={u.id}>{u.etiqueta}</option>
              ))}
            </select>
          </div>
        </>
      )}
    </div>
  )
}