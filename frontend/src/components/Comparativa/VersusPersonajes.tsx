import { Fragment } from 'react'
import styles from './VersusPersonajes.module.css'
import type { PersonajeComparado } from '../../api/feed'

interface Props {
  personajes: PersonajeComparado[]
  obraSlug: string
}

// «Luffy vs Kaido»: cada nombre enlaza a la ficha del personaje en el contexto de la obra.
export default function VersusPersonajes({ personajes, obraSlug }: Props) {
  if (personajes.length < 2) return null
  return (
    <p className={styles.versus}>
      {personajes.map((p, i) => (
        <Fragment key={p.id}>
          {i > 0 && <span className={styles.vs}>vs</span>}
          <a className={styles.personaje} href={`/narrative/personaje/${p.id}/?obra=${encodeURIComponent(obraSlug)}`}>
            {p.nombre}
          </a>
        </Fragment>
      ))}
    </p>
  )
}