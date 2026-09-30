import Header from './components/Header/Header'
import CategoriaLandingView from './components/ObraLanding/CategoriaLandingView'
import BottomNav from './components/BottomNav/BottomNav'

interface Props {
  categoriaId: number
}

export default function CategoriaLandingApp({ categoriaId }: Props) {
  return (
    <>
      <Header />
      <main className="container">
        <CategoriaLandingView categoriaId={categoriaId} />
      </main>
      <BottomNav />
    </>
  )
}