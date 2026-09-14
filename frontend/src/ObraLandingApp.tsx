import Header from './components/Header/Header'
import ObraLandingView from './components/ObraLanding/ObraLandingView'
import BottomNav from './components/BottomNav/BottomNav'

interface Props {
  obraSlug: string
}

export default function ObraLandingApp({ obraSlug }: Props) {
  return (
    <>
      <Header />
      <main className="container">
        <ObraLandingView obraSlug={obraSlug} />
      </main>
      <BottomNav />
    </>
  )
}