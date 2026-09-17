import { useEffect, useRef, useState } from 'react'

interface MensajeEntrante {
  id: number
  text: string
  sender: string
  created_at: string
}

interface ReaccionEntrante {
  type: 'reaction'
  message_id: number
  counts: Record<string, number>
}

export interface ChatSocketMessage {
  id: number
  text: string
  sender: string
  created_at: string
}

/** Réplica de messages_ws.js: conecta a /ws/chat/<username>/, reconecta
 * cada segundo si se cierra. Devuelve la lista de mensajes recibidos
 * por el socket (no el historial inicial, que se carga aparte vía
 * REST), una función para enviar un mensaje nuevo, y el mapa de
 * conteos de reacciones actualizado en vivo cuando el otro
 * participante reacciona (o cuando reaccionas tú mismo, ya que el
 * servidor reenvía el evento a toda la sala, incluido el emisor). */
export function useChatSocket(otherUsername: string) {
  const [mensajesSocket, setMensajesSocket] = useState<ChatSocketMessage[]>([])
  const [reaccionesEnVivo, setReaccionesEnVivo] = useState<Record<number, Record<string, number>>>({})
  const socketRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    let reconectarTimeout: ReturnType<typeof setTimeout> | null = null
    let cerradoManualmente = false

    function conectar() {
      const protocolo = window.location.protocol === 'https:' ? 'wss://' : 'ws://'
      const socket = new WebSocket(`${protocolo}${window.location.host}/ws/chat/${otherUsername}/`)
      socketRef.current = socket

      socket.onmessage = (e) => {
        const data: MensajeEntrante | ReaccionEntrante = JSON.parse(e.data)

        if ('type' in data && data.type === 'reaction') {
          setReaccionesEnVivo((prev) => ({ ...prev, [data.message_id]: data.counts }))
          return
        }

        setMensajesSocket((prev) => [...prev, data as MensajeEntrante])
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

  return { mensajesSocket, enviarMensaje, reaccionesEnVivo }
}