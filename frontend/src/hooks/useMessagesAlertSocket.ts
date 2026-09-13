import { useEffect, useRef } from 'react'

interface MensajeAlerta {
  type: 'new_message' | 'reset'
  count?: number
}

/** Réplica de messages_alert_ws.js: conecta a /ws/messages/, notifica
 * incrementos o reseteos del contador global de mensajes no leídos.
 * Se usa en el Header para mantener el badge del avatar actualizado
 * en tiempo real, sin recargar la página. */
export function useMessagesAlertSocket(onAlerta: (delta: number | 'reset') => void) {
  const callbackRef = useRef(onAlerta)
  callbackRef.current = onAlerta

  useEffect(() => {
    let socket: WebSocket | null = null
    let reconectarTimeout: ReturnType<typeof setTimeout> | null = null
    let cerradoManualmente = false

    function conectar() {
      const protocolo = window.location.protocol === 'https:' ? 'wss://' : 'ws://'
      socket = new WebSocket(`${protocolo}${window.location.host}/ws/messages/`)

      socket.onmessage = (e) => {
        const data: MensajeAlerta = JSON.parse(e.data)
        if (data.type === 'new_message') {
          callbackRef.current(data.count ?? 1)
        } else if (data.type === 'reset') {
          callbackRef.current('reset')
        }
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