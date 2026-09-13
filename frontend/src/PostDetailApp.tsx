import Header from './components/Header/Header'
import PostDetailView from './components/PostDetail/PostDetailView'
import BottomNav from './components/BottomNav/BottomNav'

interface Props {
  postId: number
}

export default function PostDetailApp({ postId }: Props) {
  return (
    <>
      <Header />
      <main className="container">
        <PostDetailView postId={postId} />
      </main>
      <BottomNav />
    </>
  )
}