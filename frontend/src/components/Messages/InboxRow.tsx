import styles from './InboxRow.module.css'
import type { InboxItem } from '../../api/messages'

interface Props {
  item: InboxItem
}

export default function InboxRow({ item }: Props) {
  return (
    <a className={styles.row} href={`/mensajes/chat-react/${item.username}/`}>
      <img className={styles.avatar} src={item.avatar} alt="" />
      <div className={styles.info}>
        <div className={styles.username}>@{item.username}</div>
        {item.last_message && <div className={styles.lastMessage}>{item.last_message}</div>}
      </div>
      {item.unread_count > 0 && <span className={styles.badge}>{item.unread_count}</span>}
    </a>
  )
}