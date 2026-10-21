import styles from './InboxRow.module.css'
import type { InboxItem } from '../../api/messages'

interface Props {
  item: InboxItem
}

export default function InboxRow({ item }: Props) {
  return (
    <a className={styles.row} href={`/mensajes/${item.username}/`}>
      <img className={styles.avatar} src={item.avatar} alt="" width={44} height={44} loading="lazy" decoding="async" />
      <div className={styles.info}>
        <div className={styles.username}>@{item.username}</div>
        {item.last_message && <div className={styles.lastMessage}>{item.last_message}</div>}
      </div>
      {item.unread_count > 0 && <span className={styles.badge}>{item.unread_count}</span>}
    </a>
  )
}