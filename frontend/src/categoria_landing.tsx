import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import CategoriaLandingApp from './CategoriaLandingApp'
import './styles/global.css'

const container = document.getElementById('root')
if (!container) {
  throw new Error('No se encontró el elemento #root en el DOM.')
}

const categoriaIdRaw = container.dataset.categoriaId
if (!categoriaIdRaw) {
  throw new Error('Falta el data-categoria-id en el DOM.')
}

createRoot(container).render(
  <StrictMode>
    <CategoriaLandingApp categoriaId={Number(categoriaIdRaw)} />
  </StrictMode>
)