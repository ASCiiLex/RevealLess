import { useMemo, useState } from 'react'
import Header from './components/Header/Header'
import Tabs from './components/Carousel/Tabs'
import Carousel from './components/Carousel/Carousel'
import Feed from './components/Feed/Feed'
import BottomNav from './components/BottomNav/BottomNav'
import { CatalogViewProvider } from './context/CatalogViewContext'

export default function App() {
  const filtroExterno = useMemo(() => {
    const params = new URLSearchParams(window.location.search)
    const obra = params.get('obra')
    const hashtag = params.get('hashtag')
    const tema = params.get('tema')
    const personaje = params.get('personaje')
    if (obra) return { tipo: 'obra' as const, valor: obra }
    if (hashtag) return { tipo: 'hashtag' as const, valor: hashtag }
    if (tema) return { tipo: 'tema' as const, valor: tema }
    if (personaje) return { tipo: 'personaje' as const, valor: personaje }
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