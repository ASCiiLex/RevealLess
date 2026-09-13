import Header from './components/Header/Header'
import FollowListView from './components/Follows/FollowListView'
import BottomNav from './components/BottomNav/BottomNav'

interface Props {
  username: string
  tipo: 'seguidores' | 'siguiendo'
}

export default function FollowListApp({ username, tipo }: Props) {
  return (
    <>
      <Header />
      <main className="container">
        <FollowListView username={username} tipo={tipo} />
      </main>
      <BottomNav />
    </>
  )
}