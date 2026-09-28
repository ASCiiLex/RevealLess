import { useEffect, useState } from 'react'
import styles from './ProfileView.module.css'
import botones from '../../styles/botones.module.css'
import { fetchProfile, type ProfileDetail } from '../../api/profile'
import { seguirUsuario, dejarDeSeguirUsuario } from '../../api/follow'

interface Props {
  username: string
}

export default function ProfileView({ username }: Props) {
  const [profile, setProfile] = useState<ProfileDetail | null>(null)

  useEffect(() => {
    fetchProfile(username).then(setProfile)
  }, [username])

  if (!profile) {
    return null
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <img className={styles.avatar} src={profile.avatar_url} alt="" />
        <div className={styles.info}>
          <h1 className={styles.username}>{profile.username}</h1>
          {profile.bio && <p className={styles.bio}>{profile.bio}</p>}
          {profile.interests && <p className={styles.interests}>🏷️ {profile.interests}</p>}

          <div className={styles.stats}>
            <span><strong>{profile.posts.length}</strong> publicaciones</span>
            <a href={`/follows/${profile.username}/seguidores/`}>
              <strong>{profile.followers_count}</strong> seguidores
            </a>
            <a href={`/follows/${profile.username}/siguiendo/`}>
              <strong>{profile.following_count}</strong> seguidos
            </a>
          </div>

          <div className={styles.actions}>
            {profile.is_own_profile ? (
              <a className={botones.secundario} href="/perfil/editar/">Editar perfil</a>
            ) : (
              <FollowActions username={profile.username} isFollowingInicial={profile.is_following} />
            )}
          </div>
        </div>
      </div>

      {profile.posts.length === 0 ? (
        <p className={styles.empty}>
          {profile.has_hidden_posts
            ? 'Las publicaciones de este usuario aún no son visibles para ti.'
            : 'Este usuario aún no tiene publicaciones.'}
        </p>
      ) : (
        <div className={styles.grid}>
          {profile.posts.map((post) => (
            <a key={post.id} className={styles.gridItem} href={`/posts/${post.id}/`}>
              <img className={styles.gridImage} src={post.image_url} alt="" />
            </a>
          ))}
        </div>
      )}
    </div>
  )
}

function FollowActions({
  username,
  isFollowingInicial,
}: {
  username: string
  isFollowingInicial: boolean
}) {
  const [siguiendo, setSiguiendo] = useState(isFollowingInicial)
  const [cargando, setCargando] = useState(false)

  async function handleToggle() {
    if (cargando) return
    setCargando(true)
    try {
      if (siguiendo) {
        await dejarDeSeguirUsuario(username)
        setSiguiendo(false)
      } else {
        await seguirUsuario(username)
        setSiguiendo(true)
      }
    } finally {
      setCargando(false)
    }
  }

  return (
    <>
      {siguiendo ? (
        <button
          type="button"
          className={botones.activo}
          onClick={handleToggle}
          disabled={cargando}
          aria-label={`Dejar de seguir a ${username}`}
        >
          <span className={botones.enReposo} aria-hidden="true">✓ Siguiendo</span>
          <span className={botones.alPasar} aria-hidden="true">Dejar de seguir</span>
        </button>
      ) : (
        <button type="button" className={botones.primario} onClick={handleToggle} disabled={cargando}>
          Seguir
        </button>
      )}
      <a className={botones.secundario} href={`/mensajes/${username}/`}>
        Enviar mensaje
      </a>
    </>
  )
}