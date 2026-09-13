import Header from './components/Header/Header'
import PublicarFlow from './components/Publicar/PublicarFlow'
import BottomNav from './components/BottomNav/BottomNav'

export default function PublicarApp() {
  return (
    <>
      <Header />
      <main className="container">
        <PublicarFlow />
      </main>
      <BottomNav />
    </>
  )
}