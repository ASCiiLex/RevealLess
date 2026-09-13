import Header from './components/Header/Header'
import ProfileView from './components/Profile/ProfileView'
import BottomNav from './components/BottomNav/BottomNav'

interface Props {
  username: string
}

export default function ProfileApp({ username }: Props) {
  return (
    <>
      <Header />
      <main className="container">
        <ProfileView username={username} />
      </main>
      <BottomNav />
    </>
  )
}