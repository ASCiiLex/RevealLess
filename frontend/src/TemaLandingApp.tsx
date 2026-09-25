import Header from './components/Header/Header'
import TemaLandingView from './components/ObraLanding/TemaLandingView'
import BottomNav from './components/BottomNav/BottomNav'

interface Props {
  temaId: number
}

export default function TemaLandingApp({ temaId }: Props) {
  return (
    <>
      <Header />
      <main className="container">
        <TemaLandingView temaId={temaId} />
      </main>
      <BottomNav />
    </>
  )
}