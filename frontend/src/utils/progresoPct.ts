// Espejo de calcular_progreso_pct (backend): floor, y 100 solo si el progreso es completo.
export function calcularProgresoPct(ordenAbsoluto: number, longitudTotal: number): number | null {
  if (!longitudTotal) return null
  const ratio = ordenAbsoluto / longitudTotal
  const pct = ratio >= 1 ? 100 : Math.floor(ratio * 100)
  return Math.min(Math.max(pct, 0), 100)
}