import type { Me } from '../../api/me'
import { logout } from '../../api/auth'

interface Props {
  me: Me
  itemClassName: string
  logoutClassName: string
  dividerClassName: string
}

export default function AccountMenuLinks({ me, itemClassName, logoutClassName, dividerClassName }: Props) {
  function handleLogout() {
    logout()
      .then(() => {
        window.location.href = '/cuentas/login/'
      })
      .catch(() => {
        // Si falla, la sesión sigue abierta y el usuario permanece en la página.
      })
  }

  return (
    <>
      <a className={itemClassName} href={`/perfil/${me.username}/`} role="menuitem">
        Mi perfil
      </a>
      <a className={itemClassName} href="/notificaciones/react/" role="menuitem">
        Notificaciones{me.unread_notifications > 0 ? ` (${me.unread_notifications})` : ''}
      </a>
      <a className={itemClassName} href="/mensajes/" role="menuitem">
        Mensajes{me.unread_messages > 0 ? ` (${me.unread_messages})` : ''}
      </a>
      <a className={itemClassName} href="/guardados/guardados-react/" role="menuitem">
        Guardados
      </a>
      <a className={itemClassName} href="/suscripciones/" role="menuitem">
        Suscripciones
      </a>
      <hr className={dividerClassName} />
      <button
        type="button"
        className={`${itemClassName} ${logoutClassName}`}
        onClick={handleLogout}
        role="menuitem"
      >
        Cerrar sesión
      </button>
    </>
  )
}