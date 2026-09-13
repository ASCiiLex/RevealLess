import Header from './components/Header/Header'
import EditProfileForm from './components/Profile/EditProfileForm'
import BottomNav from './components/BottomNav/BottomNav'

export default function EditProfileApp() {
  return (
    <>
      <Header />
      <main className="container">
        <EditProfileForm />
      </main>
      <BottomNav />
    </>
  )
}