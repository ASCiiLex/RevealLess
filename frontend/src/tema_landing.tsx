import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import TemaLandingApp from './TemaLandingApp'
import './styles/global.css'

const container = document.getElementById('root')
if (!container) {
  throw new Error('No se encontró el elemento #root en el DOM.')
}

const temaIdRaw = container.dataset.temaId
if (!temaIdRaw) {
  throw new Error('Falta el data-tema-id en el DOM.')
}

createRoot(container).render(
  <StrictMode>
    <TemaLandingApp temaId={Number(temaIdRaw)} />
  </StrictMode>
)