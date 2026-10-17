import { useEffect, useRef, useState } from 'react'
import type { ChatMessage } from '../api/messages'

interface ReaccionEntrante {
  type: 'reaction'
  message_id: number
  reaccion: string | null
}

/** Conecta a /ws/chat/<username>/ y reconecta cada segundo si se cierra. Devuelve los mensajes
 * llegados por el socket (el historial se carga aparte), la función de envío y la reacción en vivo
 * de cada mensaje: el servidor la reenvía a toda la sala, incluido quien reacciona. */
export function useChatSocket(otherUsername: string) {
  const [mensajesSocket, setMensajesSocket] = useState<ChatMessage[]>([])
  const [reaccionesEnVivo, setReaccionesEnVivo] = useState<Record<number, string | null>>({})
  const socketRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    let reconectarTimeout: ReturnType<typeof setTimeout> | null = null
    let cerradoManualmente = false

    function conectar() {
      const protocolo = window.location.protocol === 'https:' ? 'wss://' : 'ws://'
      const socket = new WebSocket(`${protocolo}${window.location.host}/ws/chat/${otherUsername}/`)
      socketRef.current = socket

      socket.onmessage = (e) => {
        const data: ChatMessage | ReaccionEntrante = JSON.parse(e.data)

        if ('type' in data && data.type === 'reaction') {
          setReaccionesEnVivo((prev) => ({ ...prev, [data.message_id]: data.reaccion }))
          return
        }

        setMensajesSocket((prev) => [...prev, data as ChatMessage])
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

  /** Refleja al momento la respuesta propia, sin esperar al eco del socket. */
  function fijarReaccion(messageId: number, reaccion: string | null) {
    setReaccionesEnVivo((prev) => ({ ...prev, [messageId]: reaccion }))
  }

  return { mensajesSocket, enviarMensaje, reaccionesEnVivo, fijarReaccion }
}