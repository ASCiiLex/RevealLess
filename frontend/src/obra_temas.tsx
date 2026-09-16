import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import ObraTemasApp from './ObraTemasApp'
import './styles/global.css'

const container = document.getElementById('root')
if (!container) {
  throw new Error('No se encontró el elemento #root en el DOM.')
}

const obraSlug = container.dataset.obraSlug
if (!obraSlug) {
  throw new Error('Falta el data-obra-slug en el DOM.')
}

createRoot(container).render(
  <StrictMode>
    <ObraTemasApp obraSlug={obraSlug} />
  </StrictMode>
)