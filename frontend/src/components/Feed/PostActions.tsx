import styles from './PostActions.module.css'
import ReactionBar from './ReactionBar'

interface Props {
  postId: number
  reaccionInicial: string | null
  totalesIniciales?: Record<string, number> | null
}

export default function PostActions({ postId, reaccionInicial, totalesIniciales }: Props) {
  return (
    <div className={styles.actions}>
      <ReactionBar targetId={postId} reaccionInicial={reaccionInicial} totalesIniciales={totalesIniciales} />
    </div>
  )
}