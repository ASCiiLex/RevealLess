import { useEffect, useRef, useState } from 'react'
import styles from './ChatView.module.css'
import ReactionBar from '../Feed/ReactionBar'
import { fetchChatHistory, type ChatMessage } from '../../api/messages'
import { useChatSocket } from '../../hooks/useChatSocket'

interface Props {
  username: string
}

interface MensajeUnificado {
  id: number
  text: string
  sender: string
  created_at: string
  user_reaction?: string | null
}

export default function ChatView({ username }: Props) {
  const [historial, setHistorial] = useState<ChatMessage[] | null>(null)
  const [texto, setTexto] = useState('')
  const chatBoxRef = useRef<HTMLDivElement>(null)

  const { mensajesSocket, enviarMensaje, reaccionesEnVivo } = useChatSocket(username)

  useEffect(() => {
    fetchChatHistory(username).then((data) => {
      setHistorial(data.messages)
    })
  }, [username])

  const mensajes: MensajeUnificado[] = [
    ...(historial ?? []),
    ...mensajesSocket,
  ]

  useEffect(() => {
    chatBoxRef.current?.scrollTo({ top: chatBoxRef.current.scrollHeight })
  }, [mensajes.length])

  function handleEnviar() {
    if (!texto.trim()) return
    enviarMensaje(texto)
    setTexto('')
  }

  if (!historial) {
    return null
  }

  return (
    <div className={styles.wrapper}>
      <h1 className={styles.title}>Chat con {username}</h1>

      <div className={styles.chatBox} ref={chatBoxRef}>
        {mensajes.length === 0 ? (
          <p className={styles.empty}>No hay mensajes todavía.</p>
        ) : (
          mensajes.map((msg, i) => (
            <div
              key={msg.id ?? i}
              className={`${styles.message} ${msg.sender === username ? styles.received : styles.sent}`}
            >
              {msg.text}
              <div className={styles.time}>
                {new Date(msg.created_at).toLocaleString()}
              </div>
              {msg.id && (
                <ReactionBar
                  targetId={msg.id}
                  target="message"
                  reaccionInicial={msg.user_reaction ?? null}
                  totalesEnVivo={reaccionesEnVivo[msg.id]}
                  variante="sutil"
                />
              )}
            </div>
          ))
        )}
      </div>

      <div className={styles.inputRow}>
        <input
          className={styles.input}
          type="text"
          placeholder="Escribe un mensaje..."
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
              handleEnviar()
            }
          }}
        />
        <button className={styles.sendButton} onClick={handleEnviar}>
          Enviar
        </button>
      </div>
    </div>
  )
}