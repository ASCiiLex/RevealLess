import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import ChatApp from './ChatApp'
import './styles/global.css'

const container = document.getElementById('root')
if (!container) {
  throw new Error('No se encontró el elemento #root en el DOM.')
}

const username = container.dataset.username
if (!username) {
  throw new Error('Falta el data-username en el DOM.')
}

createRoot(container).render(
  <StrictMode>
    <ChatApp username={username} />
  </StrictMode>
)