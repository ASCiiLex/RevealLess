import { useEffect, useRef } from 'react'
import type { NotificationItem } from '../api/notifications'

interface MensajeWebSocket {
  id: number
  actor: string
  verb: string
  avatar: string
  url: string
  created_at: string
}

/** Réplica de notifications_ws.js: conecta a /ws/notifications/, se
 * reconecta automáticamente cada segundo si se cierra la conexión
 * (mismo comportamiento que el JS original), y entrega cada mensaje
 * nuevo vía el callback onNuevaNotificacion. */
export function useNotificationSocket(onNuevaNotificacion: (item: NotificationItem) => void) {
  const callbackRef = useRef(onNuevaNotificacion)
  callbackRef.current = onNuevaNotificacion

  useEffect(() => {
    let socket: WebSocket | null = null
    let reconectarTimeout: ReturnType<typeof setTimeout> | null = null
    let cerradoManualmente = false

    function conectar() {
      const protocolo = window.location.protocol === 'https:' ? 'wss://' : 'ws://'
      socket = new WebSocket(`${protocolo}${window.location.host}/ws/notifications/`)

      socket.onmessage = (e) => {
        const data: MensajeWebSocket = JSON.parse(e.data)
        callbackRef.current({
          id: data.id,
          actor: data.actor,
          avatar: data.avatar,
          verb: data.verb,
          url: data.url,
          created_at: data.created_at,
          seen: false,
        })
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
      socket?.close()
    }
  }, [])
}