import { Fragment, useCallback, useEffect, useRef, useState } from 'react'
import styles from './Comparativa.module.css'
import BuscadorLocal, { type BuscadorItem } from './BuscadorLocal'
import { buscarUnidades } from '../../api/suscripciones'
import { fetchObrasPublicar, fetchPersonajesPublicar, type ObraPublicable } from '../../api/publicar'

export interface PersonajeElegido {
  id: number
  nombre: string
  // De la obra comparada: se descarta si se cambia esa obra.
  deOtraObra: boolean
}

export interface EstadoComparativa {
  activa: boolean
  obra: ObraPublicable | null
  frontera: { id: number | null; label: string | null }
  personajes: PersonajeElegido[]
}

export const COMPARATIVA_VACIA: EstadoComparativa = {
  activa: false,
  obra: null,
  frontera: { id: null, label: null },
  personajes: [],
}

export const MAX_COMPARADOS = 4

export function comparativaIncompleta(c: EstadoComparativa): boolean {
  return c.activa && ((c.obra !== null && c.frontera.id === null) || c.personajes.length === 1)
}

interface Props {
  obraSlug: string | null
  valor: EstadoComparativa
  onChange: (valor: EstadoComparativa) => void
}

export default function Comparativa({ obraSlug, valor, onChange }: Props) {
  const [obras, setObras] = useState<ObraPublicable[] | null>(null)
  const origen = useRef(new Map<number, boolean>())

  useEffect(() => {
    if (valor.activa && obras === null) {
      fetchObrasPublicar()
        .then((datos) => setObras(datos.obras))
        .catch(() => setObras([]))
    }
  }, [valor.activa, obras])

  const otraSlug = valor.obra?.slug ?? null
  const otraTitulo = valor.obra?.titulo ?? ''
  const idsElegidos = valor.personajes.map((p) => p.id).join(',')

  // Referencias estables: BuscadorLocal relanza la búsqueda si cambia su prop buscar.
  const buscarFrontera = useCallback(
    (q: string) => (otraSlug ? buscarUnidades(otraSlug, q) : Promise.resolve([])),
    [otraSlug]
  )

  const buscarPersonajes = useCallback(
    async (q: string): Promise<BuscadorItem[]> => {
      if (!obraSlug) return []
      const elegidos = new Set(idsElegidos ? idsElegidos.split(',').map(Number) : [])
      const [propios, ajenos] = await Promise.all([
        fetchPersonajesPublicar(obraSlug, q),
        otraSlug ? fetchPersonajesPublicar(otraSlug, q) : Promise.resolve([]),
      ])
      const items: BuscadorItem[] = []
      for (const p of propios) {
        if (elegidos.has(p.id) || origen.current.get(p.id) === false) continue
        origen.current.set(p.id, false)
        items.push({ id: p.id, label: p.nombre })
      }
      for (const p of ajenos) {
        if (elegidos.has(p.id) || items.some((i) => i.id === p.id)) continue
        origen.current.set(p.id, true)
        items.push({ id: p.id, label: `${p.nombre} · ${otraTitulo}` })
      }
      return items
    },
    [obraSlug, otraSlug, otraTitulo, idsElegidos]
  )

  function elegirObra(slug: string) {
    const obra = (obras ?? []).find((o) => o.slug === slug) ?? null
    onChange({
      ...valor,
      obra,
      frontera: { id: null, label: null },
      personajes: valor.personajes.filter((p) => !p.deOtraObra),
    })
  }

  function anadirPersonaje(id: number | null, label: string | null) {
    if (id === null || !label || valor.personajes.some((p) => p.id === id)) return
    const deOtraObra = origen.current.get(id) === true
    const nombre = deOtraObra ? label.replace(` · ${otraTitulo}`, '') : label
    onChange({ ...valor, personajes: [...valor.personajes, { id, nombre, deOtraObra }] })
  }

  function quitarPersonaje(id: number) {
    onChange({ ...valor, personajes: valor.personajes.filter((p) => p.id !== id) })
  }

  const otras = (obras ?? []).filter((o) => o.slug !== obraSlug)

  return (
    <div className={styles.comparativa}>
      <label className={styles.toggle}>
        <input
          type="checkbox"
          checked={valor.activa}
          onChange={(e) => onChange({ ...valor, activa: e.target.checked })}
        />
        Post comparativo
      </label>

      {valor.activa && (
        <div className={styles.panel}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="comparar-obra">Comparar con otra obra (opcional)</label>
            <select
              id="comparar-obra"
              className={styles.select}
              value={otraSlug ?? ''}
              onChange={(e) => elegirObra(e.target.value)}
            >
              <option value="">Ninguna: misma obra</option>
              {otras.map((o) => (
                <option key={o.slug} value={o.slug}>{o.titulo}</option>
              ))}
            </select>
          </div>

          {valor.obra && (
            <div className={styles.field}>
              <label className={styles.label} htmlFor="comparar-frontera">
                Frontera de spoiler en {valor.obra.titulo}
              </label>
              <BuscadorLocal
                id="comparar-frontera"
                value={valor.frontera.id}
                valueLabel={valor.frontera.label}
                onChange={(id, label) => onChange({ ...valor, frontera: { id, label } })}
                placeholder="Buscar unidad..."
                buscar={buscarFrontera}
              />
              <span className={styles.hint}>
                Solo lo verá quien haya llegado aquí en {valor.obra.titulo} y a la frontera de la obra principal.
              </span>
            </div>
          )}

          <div className={styles.field}>
            <label className={styles.label} htmlFor="comparar-personajes">
              Personajes enfrentados (opcional, de 2 a {MAX_COMPARADOS})
            </label>
            {valor.personajes.length > 0 && (
              <div className={styles.chips}>
                {valor.personajes.map((p, i) => (
                  <Fragment key={p.id}>
                    {i > 0 && <span className={styles.vs}>vs</span>}
                    <span className={styles.chip}>
                      {p.nombre}
                      <button
                        type="button"
                        className={styles.chipQuitar}
                        onClick={() => quitarPersonaje(p.id)}
                        aria-label={`Quitar a ${p.nombre}`}
                      >
                        ×
                      </button>
                    </span>
                  </Fragment>
                ))}
              </div>
            )}
            {valor.personajes.length < MAX_COMPARADOS && (
              <BuscadorLocal
                id="comparar-personajes"
                value={null}
                valueLabel={null}
                onChange={anadirPersonaje}
                placeholder="Buscar personaje..."
                buscar={buscarPersonajes}
              />
            )}
            <span className={styles.hint}>
              {valor.personajes.length === 1
                ? 'Añade al menos otro personaje.'
                : 'Solo aparecen los que ya conoces. La frontera se ajusta para que quien lo lea también los conozca.'}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}