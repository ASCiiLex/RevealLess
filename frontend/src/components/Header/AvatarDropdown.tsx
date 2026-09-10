import { useEffect, useRef, useState } from 'react'
import styles from './AvatarDropdown.module.css'
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
          <a className={styles.item} href={`/perfil/${me.username}/`} role="menuitem">
            Mi perfil
          </a>
          <a className={styles.item} href="/notificaciones/" role="menuitem">
            Notificaciones
          </a>
          <a className={styles.item} href="/mensajes/" role="menuitem">
            Mensajes
          </a>
          <a className={styles.item} href="/guardados/" role="menuitem">
            Guardados
          </a>
          <hr className={styles.divider} />
          <a className={`${styles.item} ${styles.logout}`} href="/cuentas/logout/" role="menuitem">
            Cerrar sesión
          </a>
        </div>
      )}
    </div>
  )
}