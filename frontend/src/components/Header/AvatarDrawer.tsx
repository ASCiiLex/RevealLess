import { useEffect, useState } from 'react'
import styles from './AvatarDrawer.module.css'
import AccountMenuLinks from './AccountMenuLinks'
import type { Me } from '../../api/me'

interface Props {
  me: Me
  onClose: () => void
}

const TRANSITION_MS = 200

export default function AvatarDrawer({ me, onClose }: Props) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    // Monta cerrado (transform: translateX(100%)) y, un frame después,
    // activa la clase abierta -> el navegador anima la transición.
    const id = requestAnimationFrame(() => setVisible(true))
    return () => cancelAnimationFrame(id)
  }, [])

  function handleClose() {
    setVisible(false)
    setTimeout(onClose, TRANSITION_MS)
  }

  return (
    <>
      <div
        className={`${styles.overlay} ${visible ? styles.overlayOpen : ''}`}
        onClick={handleClose}
      />
      <div className={`${styles.drawer} ${visible ? styles.drawerOpen : ''}`} role="menu">
        <button className={styles.close} onClick={handleClose} aria-label="Cerrar menú">
          ✕
        </button>
        <div className={styles.header}>
          <div className={styles.identity}>
            <img className={styles.avatarImg} src={me.avatar_url} alt="" />
            <span className={styles.username}>@{me.username}</span>
          </div>
        </div>
        <AccountMenuLinks
          me={me}
          itemClassName={styles.item}
          logoutClassName={styles.logout}
          dividerClassName={styles.divider}
        />
      </div>
    </>
  )
}