// Móvil según el propio navegador, no según la pantalla táctil: un portátil táctil con ratón no lo es.
export function esMovil(): boolean {
  const datos = (navigator as Navigator & { userAgentData?: { mobile?: boolean } }).userAgentData
  if (typeof datos?.mobile === 'boolean') return datos.mobile
  return /Mobi|iPhone|iPod/i.test(navigator.userAgent)
}