// Espejo de calcular_progreso_pct y longitudes_principales (backend).
export const TIPO_PREVIO = 'previo'

interface UnidadOrden {
  id: number
  padre?: number | null
  tipo: string
  orden_inicio: number
  orden_fin: number
}

// floor, y 100 solo si el progreso es completo.
export function calcularProgresoPct(ordenAbsoluto: number, longitudTotal: number): number | null {
  if (!longitudTotal) return null
  const ratio = ordenAbsoluto / longitudTotal
  const pct = ratio >= 1 ? 100 : Math.floor(ratio * 100)
  return Math.min(Math.max(pct, 0), 100)
}

// Hojas en orden de consumo: el progreso avanza por ellas, nunca por bloques.
export function hojasDe<T extends UnidadOrden>(unidades: T[]): T[] {
  const padres = new Set(unidades.map((u) => u.padre).filter((p): p is number => typeof p === 'number'))
  return unidades.filter((u) => !padres.has(u.id)).sort((a, b) => a.orden_inicio - b.orden_inicio)
}

// Tipo de hoja más frecuente sin contar previos (episodio en un anime, capítulo en un manga).
// Empate: el que llega más lejos. null si solo hay previos.
export function tipoPrincipal(hojas: UnidadOrden[]): string | null {
  const datos = new Map<string, { total: number; fin: number }>()
  for (const h of hojas) {
    if (h.tipo === TIPO_PREVIO) continue
    const d = datos.get(h.tipo) ?? { total: 0, fin: 0 }
    datos.set(h.tipo, { total: d.total + 1, fin: Math.max(d.fin, h.orden_fin) })
  }
  let principal: string | null = null
  let mejor = { total: 0, fin: 0 }
  for (const [tipo, d] of datos) {
    if (d.total > mejor.total || (d.total === mejor.total && d.fin > mejor.fin)) {
      principal = tipo
      mejor = d
    }
  }
  return principal
}

// Longitud para el porcentaje: hasta la última hoja del tipo principal; con solo previos, la obra entera.
export function longitudPrincipal(unidades: UnidadOrden[]): number {
  const hojas = hojasDe(unidades)
  const principal = tipoPrincipal(hojas)
  const contadas = principal ? hojas.filter((h) => h.tipo === principal) : hojas
  return Math.max(0, ...contadas.map((h) => h.orden_fin))
}