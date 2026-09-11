import Header from './components/Header/Header'
import Tabs from './components/Carousel/Tabs'
import Carousel from './components/Carousel/Carousel'
import Feed from './components/Feed/Feed'
import { CatalogViewProvider } from './context/CatalogViewContext'

export default function App() {
  return (
    <CatalogViewProvider>
      <Header />
      <main className="container">
        <Tabs />
        <Carousel />
        <Feed />
      </main>
    </CatalogViewProvider>
  )
}