import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import RegisterForm from './components/Auth/RegisterForm'
import './styles/global.css'

const container = document.getElementById('root')
if (!container) {
  throw new Error('No se encontró el elemento #root en el DOM.')
}

createRoot(container).render(
  <StrictMode>
    <RegisterForm />
  </StrictMode>
)