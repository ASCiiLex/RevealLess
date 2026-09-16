import Header from './components/Header/Header'
import TemasLandingView from './components/ObraLanding/TemasLandingView'
import BottomNav from './components/BottomNav/BottomNav'

interface Props {
  obraSlug: string
}

export default function ObraTemasApp({ obraSlug }: Props) {
  return (
    <>
      <Header />
      <main className="container">
        <TemasLandingView obraSlug={obraSlug} />
      </main>
      <BottomNav />
    </>
  )
}