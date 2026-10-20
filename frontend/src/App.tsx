import { useMemo, useState } from 'react'
import Header from './components/Header/Header'
import Tabs from './components/Carousel/Tabs'
import Carousel from './components/Carousel/Carousel'
import Feed from './components/Feed/Feed'
import BottomNav from './components/BottomNav/BottomNav'
import { CatalogViewProvider } from './context/CatalogViewContext'

const FILTROS_EXTERNOS = ['obra', 'hashtag', 'tema', 'personaje', 'unidad'] as const

export default function App() {
  const filtroExterno = useMemo(() => {
    const params = new URLSearchParams(window.location.search)
    for (const tipo of FILTROS_EXTERNOS) {
      const valor = params.get(tipo)
      if (valor) return { tipo, valor }
    }
    return null
  }, [])
  // Sube al seguir/dejar de seguir desde la estantería: el feed se vuelve a pedir.
  const [versionFeed, setVersionFeed] = useState(0)

  return (
    <CatalogViewProvider>
      <Header />
      <main className="container">
        {!filtroExterno && (
          <div>
            <Tabs />
            <Carousel onCambioSuscripcion={() => setVersionFeed((v) => v + 1)} />
          </div>
        )}
        <Feed filtroExterno={filtroExterno} version={versionFeed} />
      </main>
      <BottomNav />
    </CatalogViewProvider>
  )
}