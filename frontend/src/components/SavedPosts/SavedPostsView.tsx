import { useEffect, useState } from 'react'
import styles from './SavedPostsView.module.css'
import { fetchSavedPosts, type SavedPost } from '../../api/savedPosts'

export default function SavedPostsView() {
  const [guardados, setGuardados] = useState<SavedPost[] | null>(null)

  useEffect(() => {
    fetchSavedPosts()
      .then(setGuardados)
      .catch(() => setGuardados([]))
  }, [])

  if (!guardados) {
    return null
  }

  return (
    <div className={styles.wrapper}>
      <h1 className={styles.title}>Guardados</h1>

      {guardados.length === 0 ? (
        <p className={styles.empty}>No has guardado ninguna publicación.</p>
      ) : (
        <div className={styles.grid}>
          {guardados.map((item) => (
            <a key={item.id} className={styles.gridItem} href={`/posts/${item.post_id}/`}>
              <img className={styles.gridImage} src={item.image_url} alt="" />
            </a>
          ))}
        </div>
      )}
    </div>
  )
}