import { useEffect, useState } from 'react'
import styles from './InboxView.module.css'
import InboxRow from './InboxRow'
import { fetchInbox, type InboxItem } from '../../api/messages'

export default function InboxView() {
  const [items, setItems] = useState<InboxItem[] | null>(null)

  useEffect(() => {
    fetchInbox().then(setItems)
  }, [])

  if (!items) {
    return null
  }

  return (
    <div className={styles.wrapper}>
      <h1 className={styles.title}>Mensajes</h1>

      {items.length === 0 ? (
        <p className={styles.empty}>No tienes conversaciones todavía.</p>
      ) : (
        items.map((item) => <InboxRow key={item.username} item={item} />)
      )}
    </div>
  )
}