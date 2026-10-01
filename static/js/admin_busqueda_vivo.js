// Búsqueda en vivo en los listados del admin: refresca resultados y paginación mientras se escribe.
(function () {
  const RETARDO_MS = 300
  const CONTENEDORES = ['#changelist-form', '#changelist']
  let temporizador = null
  let peticion = null

  function buscadorDelListado() {
    // El buscador del listado, no el de la barra lateral de Unfold.
    return [...document.querySelectorAll('input[name="q"]')].find((i) => !i.closest('aside, nav')) || null
  }

  function contenedorEn(doc) {
    for (const selector of CONTENEDORES) {
      const el = doc.querySelector(selector)
      if (el) return { selector, el }
    }
    return null
  }

  function reactivarWidgets() {
    // Acciones en bloque y autocompletes de list_editable del admin de Django.
    try {
      const casillas = document.querySelectorAll('tr input.action-select')
      if (casillas.length && typeof window.Actions === 'function') window.Actions(casillas)
    } catch (e) { /* Unfold puede gestionarlas con Alpine */ }
    try {
      const $ = window.django && window.django.jQuery
      if ($ && $.fn.djangoAdminSelect2) $('.admin-autocomplete').not('[name*=__prefix__]').djangoAdminSelect2()
    } catch (e) { /* sin autocompletes */ }
  }

  async function buscar(input) {
    const url = new URL(window.location.href)
    const valor = input.value.trim()
    if (valor) url.searchParams.set('q', valor)
    else url.searchParams.delete('q')
    url.searchParams.delete('p') // vuelve a la primera página

    if (peticion) peticion.abort()
    peticion = new AbortController()

    try {
      const respuesta = await fetch(url, { signal: peticion.signal, credentials: 'same-origin' })
      if (!respuesta.ok) return
      const doc = new DOMParser().parseFromString(await respuesta.text(), 'text/html')
      const actual = contenedorEn(document)
      const nuevo = actual && doc.querySelector(actual.selector)
      if (!actual || !nuevo) {
        window.location.href = url.toString()
        return
      }

      const cursor = input.selectionStart
      actual.el.replaceWith(nuevo)
      history.replaceState(null, '', url)
      reactivarWidgets()

      // Si el buscador estaba dentro del bloque sustituido, se recupera foco y cursor.
      const reemplazo = buscadorDelListado()
      if (reemplazo && reemplazo !== input) {
        reemplazo.value = input.value
        reemplazo.focus()
        reemplazo.setSelectionRange(cursor, cursor)
        enlazar(reemplazo)
      }
    } catch (e) {
      if (e.name !== 'AbortError') console.error('Búsqueda en vivo:', e)
    }
  }

  function enlazar(input) {
    if (input.dataset.busquedaVivo) return
    input.dataset.busquedaVivo = '1'
    input.addEventListener('input', () => {
      clearTimeout(temporizador)
      temporizador = setTimeout(() => buscar(input), RETARDO_MS)
    })
  }

  document.addEventListener('DOMContentLoaded', () => {
    if (!contenedorEn(document)) return // solo en listados
    const input = buscadorDelListado()
    if (input) enlazar(input)
  })
})()