import type { ReactNode } from 'react'
import styles from './AuthLayout.module.css'
import logo from '../../assets/brand/logo-sf-ss.png'

interface Props {
  titulo: string
  children: ReactNode
  footer?: ReactNode
}

export default function AuthLayout({ titulo, children, footer }: Props) {
  return (
    <div className={styles.wrapper}>
      <img className={styles.logo} src={logo} alt="RevealLess" />
      <div className={styles.card}>
        <h1 className={styles.title}>{titulo}</h1>
        {children}
      </div>
      {footer && <div className={styles.footer}>{footer}</div>}
    </div>
  )
}