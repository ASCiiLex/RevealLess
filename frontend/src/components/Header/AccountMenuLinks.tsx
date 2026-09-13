import type { Me } from '../../api/me'

interface Props {
  me: Me
  itemClassName: string
  logoutClassName: string
  dividerClassName: string
}

export default function AccountMenuLinks({ me, itemClassName, logoutClassName, dividerClassName }: Props) {
  return (
    <>
      <a className={itemClassName} href={`/perfil/${me.username}/react/`} role="menuitem">
        Mi perfil
      </a>
      <a className={itemClassName} href="/notificaciones/react/" role="menuitem">
        Notificaciones{me.unread_notifications > 0 ? ` (${me.unread_notifications})` : ''}
      </a>
      <a className={itemClassName} href="/mensajes/react/" role="menuitem">
        Mensajes{me.unread_messages > 0 ? ` (${me.unread_messages})` : ''}
      </a>
      <a className={itemClassName} href="/guardados/guardados-react/" role="menuitem">
        Guardados
      </a>
      <a className={itemClassName} href="/suscripciones/" role="menuitem">
        Suscripciones
      </a>
      <hr className={dividerClassName} />
      <a className={`${itemClassName} ${logoutClassName}`} href="/cuentas/logout/" role="menuitem">
        Cerrar sesión
      </a>
    </>
  )
}