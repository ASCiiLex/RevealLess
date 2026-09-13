import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import FollowListApp from './FollowListApp'
import './styles/global.css'

const container = document.getElementById('root')
if (!container) {
  throw new Error('No se encontró el elemento #root en el DOM.')
}

const username = container.dataset.username
const tipo = container.dataset.tipo as 'seguidores' | 'siguiendo' | undefined

if (!username || !tipo) {
  throw new Error('Faltan data-username o data-tipo en el DOM.')
}

createRoot(container).render(
  <StrictMode>
    <FollowListApp username={username} tipo={tipo} />
  </StrictMode>
)