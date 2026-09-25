import { useEffect, useState } from 'react'
import styles from './FollowListView.module.css'
import { fetchFollowers, fetchFollowing, type FollowUserItem } from '../../api/followList'

interface Props {
  username: string
  tipo: 'seguidores' | 'siguiendo'
}

export default function FollowListView({ username, tipo }: Props) {
  const [items, setItems] = useState<FollowUserItem[] | null>(null)

  useEffect(() => {
    const fetcher = tipo === 'seguidores' ? fetchFollowers : fetchFollowing
    fetcher(username).then(setItems)
  }, [username, tipo])

  if (!items) {
    return null
  }

  const titulo = tipo === 'seguidores' ? 'Seguidores' : 'Siguiendo'
  const mensajeVacio =
    tipo === 'seguidores' ? 'Todavía no tiene seguidores.' : 'Todavía no sigue a nadie.'

  return (
    <div className={styles.wrapper}>
      <h1 className={styles.title}>{titulo}</h1>

      {items.length === 0 ? (
        <p className={styles.empty}>{mensajeVacio}</p>
      ) : (
        items.map((item) => (
          <a key={item.username} className={styles.row} href={`/perfil/${item.username}/`}>
            <img className={styles.avatar} src={item.avatar_url} alt="" />
            <span className={styles.username}>@{item.username}</span>
          </a>
        ))
      )}
    </div>
  )
}