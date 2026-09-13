import Header from './components/Header/Header'
import ChatView from './components/Messages/ChatView'
import BottomNav from './components/BottomNav/BottomNav'

interface Props {
  username: string
}

export default function ChatApp({ username }: Props) {
  return (
    <>
      <Header />
      <main className="container">
        <ChatView username={username} />
      </main>
      <BottomNav />
    </>
  )
}