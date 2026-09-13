import Header from './components/Header/Header'
import NotificationsView from './components/Notifications/NotificationsView'
import BottomNav from './components/BottomNav/BottomNav'

export default function NotificationsApp() {
  return (
    <>
      <Header />
      <main className="container">
        <NotificationsView />
      </main>
      <BottomNav />
    </>
  )
}