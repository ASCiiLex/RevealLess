import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import PostDetailApp from './PostDetailApp'
import './styles/global.css'

const container = document.getElementById('root')
if (!container) {
  throw new Error('No se encontró el elemento #root en el DOM.')
}

const postId = container.dataset.postId
if (!postId) {
  throw new Error('Falta el data-post-id en el DOM.')
}

createRoot(container).render(
  <StrictMode>
    <PostDetailApp postId={Number(postId)} />
  </StrictMode>
)