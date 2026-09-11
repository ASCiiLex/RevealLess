import { useEffect, useState } from 'react'
import styles from './AddSuscripcionForm.module.css'
import { fetchObraDetalle, crearSuscripcion, type Suscripcion, type ObraDetalle } from '../../api/suscripciones'
import type { LomoObra } from '../Carousel/Lomo'

type Nivel = 'obra' | 'unidad' | 'tema'

interface Props {
  obras: LomoObra[]
  onCreated: (suscripcion: Suscripcion) => void
  onCancel: () => void
}

export default function AddSuscripcionForm({ obras, onCreated, onCancel }: Props) {
  const [obraSlug, setObraSlug] = useState('')
  const [nivel, setNivel] = useState<Nivel>('obra')
  const [detalle, setDetalle] = useState<ObraDetalle | null>(null)
  const [unidadId, setUnidadId] = useState<number | null>(null)
  const [temaId, setTemaId] = useState<number | null>(null)
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    setDetalle(null)
    setNivel('obra')
    setUnidadId(null)
    setTemaId(null)
    if (obraSlug) {
      fetchObraDetalle(obraSlug).then(setDetalle)
    }
  }, [obraSlug])

  async function handleConfirm() {
    if (!obraSlug) return
    setGuardando(true)
    try {
      const suscripcion = await crearSuscripcion(obraSlug, {
        unidadId: nivel === 'unidad' && unidadId ? unidadId : undefined,
        temaId: nivel === 'tema' && temaId ? temaId : undefined,
      })
      onCreated(suscripcion)
    } finally {
      setGuardando(false)
    }
  }

  const puedeConfirmar =
    obraSlug !== '' &&
    (nivel === 'obra' || (nivel === 'unidad' && unidadId !== null) || (nivel === 'tema' && temaId !== null))

  return (
    <div className={styles.panel}>
      <div className={styles.field}>
        <label className={styles.label} htmlFor="obra-select">Obra</label>
        <select
          id="obra-select"
          className={styles.select}
          value={obraSlug}
          onChange={(e) => setObraSlug(e.target.value)}
        >
          <option value="">Elige una obra</option>
          {obras.map((obra) => (
            <option key={obra.id} value={obra.slug}>{obra.titulo}</option>
          ))}
        </select>
      </div>

      {detalle && (
        <>
          <div className={styles.field}>
            <span className={styles.label}>Nivel</span>
            <div className={styles.nivelOptions}>
              <button
                className={`${styles.nivelButton} ${nivel === 'obra' ? styles.nivelButtonActive : ''}`}
                onClick={() => setNivel('obra')}
              >
                Obra completa
              </button>
              <button
                className={`${styles.nivelButton} ${nivel === 'unidad' ? styles.nivelButtonActive : ''}`}
                onClick={() => setNivel('unidad')}
                disabled={detalle.unidades.length === 0}
              >
                Un arco
              </button>
              <button
                className={`${styles.nivelButton} ${nivel === 'tema' ? styles.nivelButtonActive : ''}`}
                onClick={() => setNivel('tema')}
                disabled={detalle.temas.length === 0}
              >
                Un tema
              </button>
            </div>
          </div>

          {nivel === 'unidad' && (
            <div className={styles.field}>
              <label className={styles.label} htmlFor="unidad-select">Arco</label>
              <select
                id="unidad-select"
                className={styles.select}
                value={unidadId ?? ''}
                onChange={(e) => setUnidadId(Number(e.target.value) || null)}
              >
                <option value="">Elige un arco</option>
                {detalle.unidades.map((u) => (
                  <option key={u.id} value={u.id}>{u.etiqueta}</option>
                ))}
              </select>
            </div>
          )}

          {nivel === 'tema' && (
            <div className={styles.field}>
              <label className={styles.label} htmlFor="tema-select">Tema</label>
              <select
                id="tema-select"
                className={styles.select}
                value={temaId ?? ''}
                onChange={(e) => setTemaId(Number(e.target.value) || null)}
              >
                <option value="">Elige un tema</option>
                {detalle.temas.map((t) => (
                  <option key={t.id} value={t.id}>{t.nombre}</option>
                ))}
              </select>
            </div>
          )}
        </>
      )}

      <div className={styles.actions}>
        <button className={`${styles.button} ${styles.cancel}`} onClick={onCancel}>
          Cancelar
        </button>
        <button
          className={`${styles.button} ${styles.confirm}`}
          onClick={handleConfirm}
          disabled={!puedeConfirmar || guardando}
        >
          Suscribirse
        </button>
      </div>
    </div>
  )
}