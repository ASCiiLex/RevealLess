import { Fragment } from 'react'
import styles from './LinkedText.module.css'

const TOKEN_REGEX = /([@#]\w+)/g

interface Props {
  text: string
}

export default function LinkedText({ text }: Props) {
  const partes = text.split(TOKEN_REGEX)

  return (
    <>
      {partes.map((parte, i) => {
        if (parte.startsWith('@')) {
          return (
            <a key={i} className={styles.link} href={`/perfil/${parte.slice(1)}/react/`}>
              {parte}
            </a>
          )
        }
        if (parte.startsWith('#')) {
          const tag = parte.slice(1)
          const href = `/feed/react/?hashtag=${encodeURIComponent(tag)}`
          return (
            <a key={i} className={styles.link} href={href}>
              {parte}
            </a>
          )
        }
        return <Fragment key={i}>{parte}</Fragment>
      })}
    </>
  )
}