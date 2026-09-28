import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import HeroLoginForm from '../components/Auth/HeroLoginForm'

// Sustituye el enlace de respaldo del hero por el formulario de login.
export function montarHeroLogin() {
  const contenedor = document.getElementById('hero-login')
  if (!contenedor) return

  createRoot(contenedor).render(
    <StrictMode>
      <HeroLoginForm />
    </StrictMode>
  )
}