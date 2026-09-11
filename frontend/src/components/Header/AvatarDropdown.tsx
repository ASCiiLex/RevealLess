import { useEffect, useRef, useState } from 'react'
import styles from './AvatarDropdown.module.css'
import AccountMenuLinks from './AccountMenuLinks'
import type { Me } from '../../api/me'

interface Props {
  me: Me
}

export default function AvatarDropdown({ me }: Props) {
  const [open, setOpen] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className={styles.wrapper} ref={wrapperRef}>
      <button
        className={styles.trigger}
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Cuenta"
      >
        <img className={styles.avatar} src={me.avatar_url} alt="" />
        {me.unread_count > 0 && (
          <span className={styles.badge}>{me.unread_count > 9 ? '9+' : me.unread_count}</span>
        )}
      </button>

      {open && (
        <div className={styles.menu} role="menu">
          <AccountMenuLinks
            me={me}
            itemClassName={styles.item}
            logoutClassName={styles.logout}
            dividerClassName={styles.divider}
          />
        </div>
      )}
    </div>
  )
}