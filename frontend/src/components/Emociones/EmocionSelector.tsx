import { useState } from 'react'
import styles from './EmocionSelector.module.css'
import { EMOCIONES, getEmocion } from '../../constants/emociones'

interface Props {
  value: string | null
  onChange: (clave: string | null) => void
  label?: string
  colapsable?: boolean
}

export default function EmocionSelector({
  value,
  onChange,
  label = '¿Qué te produce esto? (opcional)',
  colapsable = true,
}: Props) {
  const [abierto, setAbierto] = useState(!colapsable)
  const emocionActual = getEmocion(value ?? undefined)

  if (colapsable) {
    return (
      <div className={styles.wrapper}>
        <button
          type="button"
          className={styles.toggle}
          onClick={() => setAbierto((v) => !v)}
          aria-expanded={abierto}
        >
          <span>
            {emocionActual ? `${emocionActual.emoji} ${emocionActual.etiqueta}` : label}
          </span>
          <span className={styles.chevron} aria-hidden="true">{abierto ? '▾' : '▸'}</span>
        </button>

        {abierto && (
          <>
            <div className={styles.grid}>
              {EMOCIONES.map((emocion) => (
                <button
                  key={emocion.clave}
                  type="button"
                  className={`${styles.opcion} ${value === emocion.clave ? styles.opcionActiva : ''}`}
                  style={{ '--emocion-color': emocion.color } as React.CSSProperties}
                  onClick={() => {
                    onChange(value === emocion.clave ? null : emocion.clave)
                    setAbierto(false)
                  }}
                  aria-pressed={value === emocion.clave}
                >
                  <span className={styles.emoji} aria-hidden="true">{emocion.emoji}</span>
                  <span className={styles.etiqueta}>{emocion.etiqueta}</span>
                </button>
              ))}
            </div>
            {value && (
              <button type="button" className={styles.limpiar} onClick={() => onChange(null)}>
                Quitar emoción
              </button>
            )}
          </>
        )}
      </div>
    )
  }

  return (
    <div className={styles.wrapper}>
      <span className={styles.label}>{label}</span>
      <div className={styles.grid}>
        {EMOCIONES.map((emocion) => (
          <button
            key={emocion.clave}
            type="button"
            className={`${styles.opcion} ${value === emocion.clave ? styles.opcionActiva : ''}`}
            style={{ '--emocion-color': emocion.color } as React.CSSProperties}
            onClick={() => onChange(value === emocion.clave ? null : emocion.clave)}
            aria-pressed={value === emocion.clave}
          >
            <span className={styles.emoji} aria-hidden="true">{emocion.emoji}</span>
            <span className={styles.etiqueta}>{emocion.etiqueta}</span>
          </button>
        ))}
      </div>
      {value && (
        <button type="button" className={styles.limpiar} onClick={() => onChange(null)}>
          Quitar emoción
        </button>
      )}
    </div>
  )
}