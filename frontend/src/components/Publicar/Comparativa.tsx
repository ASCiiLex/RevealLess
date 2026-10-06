import { useEffect, useState } from 'react'
import styles from './Comparativa.module.css'
import { fetchObrasPublicar, mismaHistoria, type ModoCruce, type ObraPublicable } from '../../api/publicar'

export interface EstadoComparativa {
  activa: boolean
  obra: ObraPublicable | null
  modo: ModoCruce
}

export const COMPARATIVA_VACIA: EstadoComparativa = { activa: false, obra: null, modo: 'comparativa' }

interface InterruptorProps {
  valor: EstadoComparativa
  onChange: (valor: EstadoComparativa) => void
}

// Primera decisión del formulario: ¿post normal o comparativo?
export function InterruptorComparativa({ valor, onChange }: InterruptorProps) {
  return (
    <div className={styles.interruptor}>
      <label className={styles.toggle}>
        <input
          type="checkbox"
          checked={valor.activa}
          onChange={(e) => onChange({ ...valor, activa: e.target.checked })}
        />
        Post comparativo
      </label>
      <span className={styles.hint}>Enfrenta personajes o compara esta obra con otra.</span>
    </div>
  )
}

interface Props {
  obraPrincipalSlug: string | null
  valor: EstadoComparativa
  onChange: (valor: EstadoComparativa) => void
}

// Segunda obra y modo de visibilidad del cruce.
export default function Comparativa({ obraPrincipalSlug, valor, onChange }: Props) {
  const [obras, setObras] = useState<ObraPublicable[] | null>(null)

  useEffect(() => {
    fetchObrasPublicar()
      .then((datos) => setObras(datos.obras))
      .catch(() => setObras([]))
  }, [])

  const principal = (obras ?? []).find((o) => o.slug === obraPrincipalSlug) ?? null
  const relacionadas = Boolean(principal && valor.obra && mismaHistoria(principal, valor.obra))

  // La segunda obra no puede ser la principal; «misma escena» solo entre adaptaciones.
  useEffect(() => {
    if (!valor.obra || obras === null) return
    if (valor.obra.slug === obraPrincipalSlug) {
      onChange({ ...valor, obra: null, modo: 'comparativa' })
    } else if (valor.modo === 'misma_escena' && !relacionadas) {
      onChange({ ...valor, modo: 'comparativa' })
    }
  }, [obraPrincipalSlug, valor, relacionadas, obras, onChange])

  function elegirObra(slug: string) {
    const obra = (obras ?? []).find((o) => o.slug === slug) ?? null
    const modo: ModoCruce = principal && obra && mismaHistoria(principal, obra) ? 'misma_escena' : 'comparativa'
    onChange({ ...valor, obra, modo })
  }

  const otras = (obras ?? []).filter((o) => o.slug !== obraPrincipalSlug)

  return (
    <div className={styles.panel}>
      <div className={styles.field}>
        <label className={styles.label} htmlFor="comparar-obra">Comparar con otra obra (opcional)</label>
        <select
          id="comparar-obra"
          className={styles.select}
          value={valor.obra?.slug ?? ''}
          onChange={(e) => elegirObra(e.target.value)}
        >
          <option value="">Ninguna: comparativa dentro de la misma obra</option>
          {otras.map((o) => (
            <option key={o.slug} value={o.slug}>{o.titulo}</option>
          ))}
        </select>
      </div>

      {valor.obra && relacionadas && (
        <div className={styles.modos} role="radiogroup" aria-label="Quién puede verlo">
          <label className={styles.modo}>
            <input
              type="radio"
              name="modo-cruce"
              checked={valor.modo === 'misma_escena'}
              onChange={() => onChange({ ...valor, modo: 'misma_escena' })}
            />
            <span>
              <span className={styles.modoTitulo}>Misma escena en otro formato</span>
              <span className={styles.hint}>Basta con haberla alcanzado en una de las dos obras.</span>
            </span>
          </label>
          <label className={styles.modo}>
            <input
              type="radio"
              name="modo-cruce"
              checked={valor.modo === 'comparativa'}
              onChange={() => onChange({ ...valor, modo: 'comparativa' })}
            />
            <span>
              <span className={styles.modoTitulo}>Comparativa</span>
              <span className={styles.hint}>Hay que haber llegado en las dos obras.</span>
            </span>
          </label>
        </div>
      )}

      {valor.obra && !relacionadas && (
        <span className={styles.hint}>
          Crossover: solo lo verá quien haya llegado en las dos obras.
        </span>
      )}
    </div>
  )
}