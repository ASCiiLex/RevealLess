import Header from './components/Header/Header'
import PersonajeLandingView from './components/ObraLanding/PersonajeLandingView'
import BottomNav from './components/BottomNav/BottomNav'

interface Props {
  personajeId: number
}

export default function PersonajeLandingApp({ personajeId }: Props) {
  return (
    <div>
      <Header />
      <main className="container">
        <PersonajeLandingView personajeId={personajeId} />
      </main>
      <BottomNav />
    </div>
  )
}