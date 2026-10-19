import { createContext, useContext, useState, type ReactNode } from 'react'

export type CatalogView = 'biblioteca' | 'descubrir'

interface CatalogViewContextValue {
  view: CatalogView
  setView: (view: CatalogView) => void
  obraFiltro: number | null
  setObraFiltro: (id: number | null) => void
  // Lomo de tema seleccionado: id real del tema, no el negativo del lomo.
  temaFiltro: number | null
  setTemaFiltro: (id: number | null) => void
  personajeFiltro: number | null
  setPersonajeFiltro: (id: number | null) => void
  // El lomo seleccionado está silenciado: el feed explica por qué sale vacío.
  filtroSilenciado: boolean
  setFiltroSilenciado: (silenciado: boolean) => void
}

const CatalogViewContext = createContext<CatalogViewContextValue | null>(null)

function leerViewInicial(): CatalogView {
  const params = new URLSearchParams(window.location.search)
  return params.get('view') === 'descubrir' ? 'descubrir' : 'biblioteca'
}

export function CatalogViewProvider({ children }: { children: ReactNode }) {
  const [view, setViewState] = useState<CatalogView>(leerViewInicial)
  const [obraFiltro, setObraFiltro] = useState<number | null>(null)
  const [temaFiltro, setTemaFiltro] = useState<number | null>(null)
  const [personajeFiltro, setPersonajeFiltro] = useState<number | null>(null)
  const [filtroSilenciado, setFiltroSilenciado] = useState(false)

  function setView(nuevo: CatalogView) {
    setViewState(nuevo)
    const url = new URL(window.location.href)
    url.searchParams.set('view', nuevo)
    window.history.replaceState(null, '', url)
  }

  return (
    <CatalogViewContext.Provider
      value={{
        view,
        setView,
        obraFiltro,
        setObraFiltro,
        temaFiltro,
        setTemaFiltro,
        personajeFiltro,
        setPersonajeFiltro,
        filtroSilenciado,
        setFiltroSilenciado,
      }}
    >
      {children}
    </CatalogViewContext.Provider>
  )
}

export function useCatalogView() {
  const ctx = useContext(CatalogViewContext)
  if (!ctx) {
    throw new Error('useCatalogView debe usarse dentro de CatalogViewProvider')
  }
  return ctx
}

/** Igual que useCatalogView, pero devuelve null en vez de lanzar si no hay
 * provider — para componentes compartidos (BottomNav) que se usan tanto
 * dentro del feed (con provider) como en otras páginas React (sin él). */
export function useOptionalCatalogView() {
  return useContext(CatalogViewContext)
}