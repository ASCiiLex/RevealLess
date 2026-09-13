import { useEffect, useState } from 'react'
import styles from './NotificationsView.module.css'
import NotificationRow from './NotificationRow'
import { fetchNotifications, type NotificationItem } from '../../api/notifications'
import { useNotificationSocket } from '../../hooks/useNotificationSocket'

export default function NotificationsView() {
  const [items, setItems] = useState<NotificationItem[] | null>(null)
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)

  useEffect(() => {
    fetchNotifications(1).then((data) => {
      setItems(data.results)
      setHasNext(data.has_next)
    })
  }, [])

  useNotificationSocket((nueva) => {
    setItems((prev) => (prev ? [nueva, ...prev] : [nueva]))
  })

  async function cargarMas() {
    const siguiente = page + 1
    const data = await fetchNotifications(siguiente)
    setItems((prev) => (prev ? [...prev, ...data.results] : data.results))
    setHasNext(data.has_next)
    setPage(siguiente)
  }

  if (!items) {
    return null
  }

  return (
    <div className={styles.wrapper}>
      <h1 className={styles.title}>Notificaciones</h1>

      {items.length === 0 ? (
        <p className={styles.empty}>No tienes notificaciones todavía.</p>
      ) : (
        <>
          {items.map((item) => (
            <NotificationRow key={item.id} item={item} />
          ))}
          {hasNext && (
            <button className={styles.loadMore} onClick={cargarMas}>
              Cargar más
            </button>
          )}
        </>
      )}
    </div>
  )
}