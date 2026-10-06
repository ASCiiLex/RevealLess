import { Fragment } from 'react'
import styles from './VersusPersonajes.module.css'
import type { PersonajeComparado } from '../../api/feed'

interface Props {
  personajes: PersonajeComparado[]
  obraSlug: string
}

// «Luffy vs Kaido»: cada nombre enlaza a su ficha; los propuestos se muestran sin enlace.
export default function VersusPersonajes({ personajes, obraSlug }: Props) {
  if (personajes.length < 2) return null
  return (
    <p className={styles.versus}>
      {personajes.map((p, i) => (
        <Fragment key={p.id ?? `propuesto-${p.nombre}`}>
          {i > 0 && <span className={styles.vs}>vs</span>}
          {p.id === null ? (
            <span className={styles.pendiente} title="Personaje propuesto, pendiente de revisión">
              {p.nombre}
            </span>
          ) : (
            <a className={styles.personaje} href={`/narrative/personaje/${p.id}/?obra=${encodeURIComponent(obraSlug)}`}>
              {p.nombre}
            </a>
          )}
        </Fragment>
      ))}
    </p>
  )
}