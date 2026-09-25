import { useMemo } from 'react'
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
    if (obra) return { tipo: 'obra' as const, valor: obra }
    if (hashtag) return { tipo: 'hashtag' as const, valor: hashtag }
    if (tema) return { tipo: 'tema' as const, valor: tema }
    return null
  }, [])

  return (
    <CatalogViewProvider>
      <Header />
      <main className="container">
        {!filtroExterno && (
          <>
            <Tabs />
            <Carousel />
          </>
        )}
        <Feed filtroExterno={filtroExterno} />
      </main>
      <BottomNav />
    </CatalogViewProvider>
  )
}