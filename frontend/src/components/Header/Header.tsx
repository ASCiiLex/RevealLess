import { useEffect, useState } from 'react'
import styles from './Header.module.css'
import AvatarDropdown from './AvatarDropdown'
import AvatarDrawer from './AvatarDrawer'
import MobileSearchOverlay from './MobileSearchOverlay'
import { fetchMe, type Me } from '../../api/me'
import { useIsMobile } from '../../hooks/useIsMobile'
import logo from '../../assets/brand/logo-sf-ss.png'

export default function Header() {
  const [me, setMe] = useState<Me | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const isMobile = useIsMobile()

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
          <button
            className={styles.searchToggle}
            onClick={() => setSearchOpen((v) => !v)}
            aria-label="Buscar"
          >
            🔍
          </button>

          {me && isMobile && (
            <button
              className={styles.avatarButtonMobile}
              onClick={() => setDrawerOpen(true)}
              aria-label="Cuenta"
            >
              <img className={styles.avatarImgMobile} src={me.avatar_url} alt="" />
              {me.unread_count > 0 && (
                <span className={styles.badgeMobile}>
                  {me.unread_count > 9 ? '9+' : me.unread_count}
                </span>
              )}
            </button>
          )}

          {me && !isMobile && <AvatarDropdown me={me} />}
        </div>
      </div>

      {searchOpen && <MobileSearchOverlay onClose={() => setSearchOpen(false)} />}

      {me && isMobile && drawerOpen && (
        <AvatarDrawer me={me} onClose={() => setDrawerOpen(false)} />
      )}
    </header>
  )
}