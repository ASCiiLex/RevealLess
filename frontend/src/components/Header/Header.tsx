import { useEffect, useRef, useState } from 'react'
import styles from './Header.module.css'
import AvatarDropdown from './AvatarDropdown'
import AvatarDrawer from './AvatarDrawer'
import MobileSearchOverlay from './MobileSearchOverlay'
import SearchResults from './SearchResults'
import SugerirObraModal from '../SugerirObra/SugerirObraModal'
import { fetchMe, type Me } from '../../api/me'
import { buscar, type ResultadoBusqueda } from '../../api/buscar'
import { useIsMobile } from '../../hooks/useIsMobile'
import { useMessagesAlertSocket } from '../../hooks/useMessagesAlertSocket'
import { useNotificationSocket } from '../../hooks/useNotificationSocket'
import logo from '../../assets/brand/logo-sf-ss.png'

export default function Header() {
  const [me, setMe] = useState<Me | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [resultado, setResultado] = useState<ResultadoBusqueda | null>(null)
  // Título con el que se abre el modal de sugerir obra; null = cerrado.
  const [sugerirObra, setSugerirObra] = useState<string | null>(null)
  const isMobile = useIsMobile()
  const searchWrapperRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchMe()
      .then(setMe)
      .catch(() => setMe(null))
  }, [])

  useMessagesAlertSocket((delta) => {
    setMe((prev) => {
      if (!prev) return prev
      const nuevoUnreadMessages = delta === 'reset' ? 0 : prev.unread_messages + delta
      return {
        ...prev,
        unread_messages: nuevoUnreadMessages,
        unread_count: prev.unread_notifications + nuevoUnreadMessages,
      }
    })
  })

  // Cada notificación entrante incrementa el contador en vivo, sin recargar.
  useNotificationSocket(() => {
    setMe((prev) => {
      if (!prev) return prev
      const nuevoUnreadNotifications = prev.unread_notifications + 1
      return {
        ...prev,
        unread_notifications: nuevoUnreadNotifications,
        unread_count: nuevoUnreadNotifications + prev.unread_messages,
      }
    })
  })

  useEffect(() => {
    if (query.trim().length < 2) {
      setResultado(null)
      return
    }
    const id = setTimeout(() => {
      buscar(query.trim()).then(setResultado)
    }, 300)
    return () => clearTimeout(id)
  }, [query])

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchWrapperRef.current && !searchWrapperRef.current.contains(event.target as Node)) {
        setResultado(null)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <header className={styles.header}>
      <div className={`container ${styles.inner}`}>
        <a className={styles.logoLink} href="/feed/">
          <img className={styles.logoImg} src={logo} alt="RevealLess" />
        </a>

        <div className={styles.searchWrapper} ref={searchWrapperRef}>
          <input
            className={styles.search}
            type="search"
            placeholder="Buscar obras, categorías, temas..."
            aria-label="Buscar"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {resultado && (
            <SearchResults resultado={resultado} onSugerirObra={() => setSugerirObra(query.trim())} />
          )}
        </div>

        <div className={styles.right}>
          <a className={styles.createLink} href="/posts/post/" aria-label="Crear publicación">
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

      {sugerirObra !== null && (
        <SugerirObraModal tituloInicial={sugerirObra} onClose={() => setSugerirObra(null)} />
      )}
    </header>
  )
}