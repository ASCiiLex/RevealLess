import Header from './components/Header/Header'
import SavedPostsView from './components/SavedPosts/SavedPostsView'
import BottomNav from './components/BottomNav/BottomNav'

export default function SavedPostsApp() {
  return (
    <>
      <Header />
      <main className="container">
        <SavedPostsView />
      </main>
      <BottomNav />
    </>
  )
}