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
      <a className={itemClassName} href={`/perfil/${me.username}/`} role="menuitem">
        Mi perfil
      </a>
      <a className={itemClassName} href="/notificaciones/" role="menuitem">
        Notificaciones
      </a>
      <a className={itemClassName} href="/mensajes/" role="menuitem">
        Mensajes
      </a>
      <a className={itemClassName} href="/guardados/" role="menuitem">
        Guardados
      </a>
      <hr className={dividerClassName} />
      <a className={`${itemClassName} ${logoutClassName}`} href="/cuentas/logout/" role="menuitem">
        Cerrar sesión
      </a>
    </>
  )
}