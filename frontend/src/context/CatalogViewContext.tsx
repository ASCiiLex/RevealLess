import { createContext, useContext, useState, type ReactNode } from 'react'

export type CatalogView = 'biblioteca' | 'descubrir'

interface CatalogViewContextValue {
  view: CatalogView
  setView: (view: CatalogView) => void
  obraFiltro: number | null
  setObraFiltro: (id: number | null) => void
}

const CatalogViewContext = createContext<CatalogViewContextValue | null>(null)

export function CatalogViewProvider({ children }: { children: ReactNode }) {
  const [view, setView] = useState<CatalogView>('biblioteca')
  const [obraFiltro, setObraFiltro] = useState<number | null>(null)

  return (
    <CatalogViewContext.Provider value={{ view, setView, obraFiltro, setObraFiltro }}>
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