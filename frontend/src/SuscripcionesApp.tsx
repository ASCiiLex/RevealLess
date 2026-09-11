import Header from './components/Header/Header'
import SuscripcionesView from './components/Suscripciones/SuscripcionesView'
import BottomNav from './components/BottomNav/BottomNav'

export default function SuscripcionesApp() {
  return (
    <>
      <Header />
      <main className="container">
        <SuscripcionesView />
      </main>
      <BottomNav />
    </>
  )
}