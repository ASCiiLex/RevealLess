import { useEffect, useRef, useState } from 'react'

interface MensajeEntrante {
  text: string
  sender: string
  created_at: string
}

export interface ChatSocketMessage {
  text: string
  sender: string
  created_at: string
}

/** Réplica de messages_ws.js: conecta a /ws/chat/<username>/, reconecta
 * cada segundo si se cierra. Devuelve la lista de mensajes recibidos
 * por el socket (no el historial inicial, que se carga aparte vía
 * REST) y una función para enviar un mensaje nuevo. */
export function useChatSocket(otherUsername: string) {
  const [mensajesSocket, setMensajesSocket] = useState<ChatSocketMessage[]>([])
  const socketRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    let reconectarTimeout: ReturnType<typeof setTimeout> | null = null
    let cerradoManualmente = false

    function conectar() {
      const protocolo = window.location.protocol === 'https:' ? 'wss://' : 'ws://'
      const socket = new WebSocket(`${protocolo}${window.location.host}/ws/chat/${otherUsername}/`)
      socketRef.current = socket

      socket.onmessage = (e) => {
        const data: MensajeEntrante = JSON.parse(e.data)
        setMensajesSocket((prev) => [...prev, data])
      }

      socket.onclose = () => {
        if (!cerradoManualmente) {
          reconectarTimeout = setTimeout(conectar, 1000)
        }
      }
    }

    conectar()

    return () => {
      cerradoManualmente = true
      if (reconectarTimeout) clearTimeout(reconectarTimeout)
      socketRef.current?.close()
    }
  }, [otherUsername])

  function enviarMensaje(text: string) {
    const socket = socketRef.current
    if (!text.trim() || !socket || socket.readyState !== WebSocket.OPEN) return
    socket.send(JSON.stringify({ text }))
  }

  return { mensajesSocket, enviarMensaje }
}