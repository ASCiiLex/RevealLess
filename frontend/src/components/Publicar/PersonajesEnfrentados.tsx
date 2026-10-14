import { Fragment, useCallback, useRef } from 'react'
import styles from './Comparativa.module.css'
import BuscadorLocal, { type BuscadorItem } from './BuscadorLocal'
import { fetchPersonajesPublicar, type ObraPublicable } from '../../api/publicar'

export interface PersonajeElegido {
  // null: propuesto (aún no existe o no aparece en la búsqueda).
  id: number | null
  nombre: string
  // De la obra comparada: se descarta si se cambia esa obra.
  deOtraObra: boolean
}

export const MAX_COMPARADOS = 4

interface Props {
  obraSlug: string | null
  otraObra: ObraPublicable | null
  valor: PersonajeElegido[]
  onChange: (valor: PersonajeElegido[]) => void
}

export default function PersonajesEnfrentados({ obraSlug, otraObra, valor, onChange }: Props) {
  // Ids que llegaron desde la obra comparada en la última búsqueda.
  const deOtra = useRef(new Set<number>())

  const otraSlug = otraObra?.slug ?? null
  const otraTitulo = otraObra?.titulo ?? ''
  const sufijo = ` · ${otraTitulo}`
  const idsElegidos = valor.filter((p) => p.id !== null).map((p) => p.id).join(',')

  // Referencia estable: BuscadorLocal relanza la búsqueda si cambia su prop buscar.
  const buscar = useCallback(
    async (q: string): Promise<BuscadorItem[]> => {
      if (!obraSlug) return []
      const elegidos = new Set(idsElegidos ? idsElegidos.split(',').map(Number) : [])
      const [propios, ajenos] = await Promise.all([
        fetchPersonajesPublicar(obraSlug, q),
        otraSlug ? fetchPersonajesPublicar(otraSlug, q) : Promise.resolve([]),
      ])
      const items: BuscadorItem[] = []
      const vistos = new Set<number>()
      for (const p of propios) {
        if (elegidos.has(p.id) || vistos.has(p.id)) continue
        vistos.add(p.id)
        deOtra.current.delete(p.id)
        items.push({ id: p.id, label: p.nombre })
      }
      for (const p of ajenos) {
        if (elegidos.has(p.id) || vistos.has(p.id)) continue
        vistos.add(p.id)
        deOtra.current.add(p.id)
        items.push({ id: p.id, label: `${p.nombre} · ${otraTitulo}` })
      }
      return items
    },
    [obraSlug, otraSlug, otraTitulo, idsElegidos]
  )

  function anadir(id: number | null, label: string | null) {
    if (id === null || !label || valor.some((p) => p.id === id)) return
    const esOtra = deOtra.current.has(id)
    const nombre = esOtra && label.endsWith(sufijo) ? label.slice(0, -sufijo.length) : label
    onChange([...valor, { id, nombre, deOtraObra: esOtra }])
  }

  function proponer(texto: string) {
    const nombre = texto.trim()
    if (!nombre || valor.some((p) => p.nombre.toLowerCase() === nombre.toLowerCase())) return
    onChange([...valor, { id: null, nombre, deOtraObra: false }])
  }

  function quitar(indice: number) {
    onChange(valor.filter((_, i) => i !== indice))
  }

  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor="comparar-personajes">
        Personajes enfrentados (opcional, de 2 a {MAX_COMPARADOS})
      </label>
      {valor.length > 0 && (
        <div className={styles.chips}>
          {valor.map((p, i) => (
            <Fragment key={p.id ?? `propuesto-${p.nombre}`}>
              {i > 0 && <span className={styles.vs}>vs</span>}
              <span className={`${styles.chip} ${p.id === null ? styles.chipPropuesto : ''}`}>
                {p.nombre}{p.id === null && ' (propuesto)'}
                <button
                  type="button"
                  className={styles.chipQuitar}
                  onClick={() => quitar(i)}
                  aria-label={`Quitar a ${p.nombre}`}
                >
                  ×
                </button>
              </span>
            </Fragment>
          ))}
        </div>
      )}
      {valor.length < MAX_COMPARADOS && (
        <BuscadorLocal
          id="comparar-personajes"
          value={null}
          valueLabel={null}
          onChange={anadir}
          placeholder="Buscar o proponer personaje..."
          buscar={buscar}
          onProponer={proponer}
          textoProponer={(t) => `Proponer «${t}» como personaje nuevo`}
        />
      )}
      <span className={styles.hint}>
        {valor.length === 1
          ? 'Añade al menos otro personaje.'
          : 'Solo aparecen los que ya conoces. Si falta alguno, proponlo: se revisará antes de añadirlo.'}
      </span>
    </div>
  )
}