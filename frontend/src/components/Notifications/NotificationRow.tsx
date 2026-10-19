import styles from './NotificationRow.module.css'
import type { NotificationItem } from '../../api/notifications'

interface Props {
  item: NotificationItem
}

export default function NotificationRow({ item }: Props) {
  return (
    <a className={`${styles.row} ${!item.seen ? styles.rowUnseen : ''}`} href={item.url}>
      <img className={styles.avatar} src={item.avatar} alt="" loading="lazy" decoding="async" />
      <div>
        <div className={styles.text}>
          <strong>@{item.actor}</strong> {item.verb}
        </div>
        <div className={styles.time}>{item.seen ? '' : 'Ahora'}</div>
      </div>
    </a>
  )
}