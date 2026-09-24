import styles from './PostActions.module.css'
import ReactionBar from './ReactionBar'

interface Props {
  postId: number
  reaccionInicial: string | null
}

export default function PostActions({ postId, reaccionInicial }: Props) {
  return (
    <div className={styles.actions}>
      <ReactionBar targetId={postId} reaccionInicial={reaccionInicial} />
    </div>
  )
}