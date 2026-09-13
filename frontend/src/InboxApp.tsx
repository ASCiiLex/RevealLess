import Header from './components/Header/Header'
import InboxView from './components/Messages/InboxView'
import BottomNav from './components/BottomNav/BottomNav'

export default function InboxApp() {
  return (
    <>
      <Header />
      <main className="container">
        <InboxView />
      </main>
      <BottomNav />
    </>
  )
}