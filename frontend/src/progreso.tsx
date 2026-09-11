import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import ProgresoApp from './ProgresoApp'
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
    <ProgresoApp obraSlug={obraSlug} />
  </StrictMode>
)