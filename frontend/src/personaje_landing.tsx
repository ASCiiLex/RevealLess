import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import PersonajeLandingApp from './PersonajeLandingApp'
import './styles/global.css'

const container = document.getElementById('root')
if (!container) {
  throw new Error('No se encontró el elemento #root en el DOM.')
}

const personajeIdRaw = container.dataset.personajeId
if (!personajeIdRaw) {
  throw new Error('Falta el data-personaje-id en el DOM.')
}

createRoot(container).render(
  <StrictMode>
    <PersonajeLandingApp personajeId={Number(personajeIdRaw)} />
  </StrictMode>
)