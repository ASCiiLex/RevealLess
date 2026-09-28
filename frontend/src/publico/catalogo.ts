// Catálogo público: sinopsis exclusivas (panel flotante en escritorio) y carga "Ver más".
const ESCRITORIO = window.matchMedia('(min-width: 768px)')
const SEPARACION_PANEL_PX = 12

export function iniciarCatalogo() {
  const catalogo = document.querySelector<HTMLElement>('[data-catalogo]')
  if (!catalogo) return

  const grid = catalogo.querySelector<HTMLElement>('[data-catalogo-grid]')
  const panel = catalogo.querySelector<HTMLElement>('[data-sinopsis-panel]')
  const flecha = catalogo.querySelector<HTMLElement>('[data-sinopsis-flecha]')
  const titulo = catalogo.querySelector<HTMLElement>('[data-sinopsis-titulo]')
  const texto = catalogo.querySelector<HTMLElement>('[data-sinopsis-texto]')
  const cerrar = catalogo.querySelector<HTMLButtonElement>('[data-sinopsis-cerrar]')
  if (!grid || !panel || !flecha || !titulo || !texto || !cerrar) return

  let abierta: HTMLDetailsElement | null = null

  function ocultarPanel() {
    panel!.hidden = true
  }

  function mostrarPanel(details: HTMLDetailsElement) {
    const tarjeta = details.closest<HTMLElement>('.pl-card')
    if (!tarjeta) return

    titulo!.textContent = tarjeta.querySelector('h3')?.textContent ?? ''
    texto!.textContent = details.querySelector('p')?.textContent ?? ''

    // Ancla bajo la tarjeta más alta de la fila para no tapar ninguna.
    const fila = Array.from(grid!.children as HTMLCollectionOf<HTMLElement>)
      .filter((c) => c.offsetTop === tarjeta.offsetTop)
    const fondoFila = Math.max(...fila.map((c) => c.offsetTop + c.offsetHeight))

    panel!.style.top = `${fondoFila + SEPARACION_PANEL_PX}px`
    flecha!.style.left = `${tarjeta.offsetLeft + tarjeta.offsetWidth / 2}px`
    panel!.hidden = false
  }

  function cerrarAbierta() {
    if (abierta) abierta.open = false
  }

  // 'toggle' no burbujea: se escucha en captura.
  grid.addEventListener('toggle', (e) => {
    const details = e.target
    if (!(details instanceof HTMLDetailsElement)) return

    if (details.open) {
      if (abierta && abierta !== details) abierta.open = false
      abierta = details
      if (ESCRITORIO.matches) mostrarPanel(details)
    } else if (abierta === details) {
      abierta = null
      ocultarPanel()
    }
  }, true)

  document.addEventListener('click', (e) => {
    if (!abierta) return
    const objetivo = e.target as Node
    if (abierta.contains(objetivo) || panel.contains(objetivo)) return
    cerrarAbierta()
  })

  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape' || !abierta) return
    const summary = abierta.querySelector('summary')
    cerrarAbierta()
    summary?.focus()
  })

  cerrar.addEventListener('click', cerrarAbierta)

  function recolocar() {
    if (abierta && ESCRITORIO.matches) mostrarPanel(abierta)
    else ocultarPanel()
  }
  window.addEventListener('resize', recolocar)
  ESCRITORIO.addEventListener('change', recolocar)

  const verMas = document.querySelector<HTMLAnchorElement>('[data-ver-mas]')
  verMas?.addEventListener('click', async (e) => {
    e.preventDefault()
    if (verMas.getAttribute('aria-busy') === 'true') return

    verMas.setAttribute('aria-busy', 'true')
    verMas.textContent = 'Cargando…'
    try {
      const respuesta = await fetch(`?pagina=${verMas.dataset.siguiente}&parcial=1`)
      if (!respuesta.ok) throw new Error(String(respuesta.status))

      // HTML propio, renderizado y escapado por Django.
      grid.insertAdjacentHTML('beforeend', await respuesta.text())

      const siguiente = respuesta.headers.get('X-Pagina-Siguiente')
      if (siguiente) {
        verMas.dataset.siguiente = siguiente
        verMas.href = `?pagina=${siguiente}`
        verMas.textContent = 'Ver más obras'
      } else {
        verMas.parentElement?.remove()
      }
    } catch {
      verMas.textContent = 'No se pudo cargar. Reintentar'
    } finally {
      verMas.removeAttribute('aria-busy')
    }
  })
}