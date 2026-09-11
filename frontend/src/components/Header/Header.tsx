import { useEffect, useState } from 'react'
import styles from './Header.module.css'
import AvatarDropdown from './AvatarDropdown'
import { fetchMe, type Me } from '../../api/me'
import logo from '../../assets/brand/logo-sf-ss.png'

interface Props {
  onToggleSearch: () => void
}

export default function Header({ onToggleSearch }: Props) {
  const [me, setMe] = useState<Me | null>(null)

  useEffect(() => {
    fetchMe()
      .then(setMe)
      .catch(() => setMe(null))
  }, [])

  return (
    <header className={styles.header}>
      <div className={`container ${styles.inner}`}>
        <a className={styles.logoLink} href="/feed/">
          <img className={styles.logoImg} src={logo} alt="RevealLess" />
        </a>

        <input
          className={styles.search}
          type="search"
          placeholder="Buscar obras, temas..."
          aria-label="Buscar"
        />

        <div className={styles.right}>
          <a className={styles.createLink} href="/narrative/publicar/" aria-label="Crear publicación">
            +
          </a>
          <button className={styles.searchToggle} onClick={onToggleSearch} aria-label="Buscar">
            🔍
          </button>
          {me && <AvatarDropdown me={me} />}
        </div>
      </div>
    </header>
  )
}