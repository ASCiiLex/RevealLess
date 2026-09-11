import { useState } from 'react'
import Header from './components/Header/Header'
import MobileSearchOverlay from './components/Header/MobileSearchOverlay'
import Tabs from './components/Carousel/Tabs'
import Carousel from './components/Carousel/Carousel'
import Feed from './components/Feed/Feed'
import BottomNav from './components/BottomNav/BottomNav'
import { CatalogViewProvider } from './context/CatalogViewContext'

export default function App() {
  const [searchOpen, setSearchOpen] = useState(false)

  return (
    <CatalogViewProvider>
      <Header onToggleSearch={() => setSearchOpen((v) => !v)} />
      {searchOpen && <MobileSearchOverlay onClose={() => setSearchOpen(false)} />}
      <main className="container">
        <Tabs />
        <Carousel />
        <Feed />
      </main>
      <BottomNav />
    </CatalogViewProvider>
  )
}