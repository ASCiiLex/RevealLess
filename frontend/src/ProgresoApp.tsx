import Header from './components/Header/Header'
import ProgresoView from './components/Progreso/ProgresoView'
import BottomNav from './components/BottomNav/BottomNav'

interface Props {
  obraSlug: string
}

export default function ProgresoApp({ obraSlug }: Props) {
  return (
    <>
      <Header />
      <main className="container">
        <ProgresoView obraSlug={obraSlug} />
      </main>
      <BottomNav />
    </>
  )
}