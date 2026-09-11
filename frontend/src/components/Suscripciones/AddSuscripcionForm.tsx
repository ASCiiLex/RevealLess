import { useEffect, useState } from 'react'
import styles from './AddSuscripcionForm.module.css'
import {
  fetchObraDetalle,
  crearSuscripcion,
  crearSolicitudTema,
  type Suscripcion,
  type ObraDetalle,
} from '../../api/suscripciones'
import type { LomoObra } from '../Carousel/Lomo'

type Nivel = 'obra' | 'unidad' | 'tema'

interface Props {
  obras: LomoObra[]
  onCreated: (suscripcion: Suscripcion) => void
  onCancel: () => void
}

export default function AddSuscripcionForm({ obras, onCreated, onCancel }: Props) {
  const [obraSlug, setObraSlug] = useState('')
  const [obraId, setObraId] = useState<number | null>(null)
  const [nivel, setNivel] = useState<Nivel>('obra')
  const [detalle, setDetalle] = useState<ObraDetalle | null>(null)
  const [unidadId, setUnidadId] = useState<number | null>(null)
  const [temaId, setTemaId] = useState<number | null>(null)
  const [guardando, setGuardando] = useState(false)

  const [solicitarAbierto, setSolicitarAbierto] = useState(false)
  const [nombreSolicitud, setNombreSolicitud] = useState('')
  const [solicitudEnviada, setSolicitudEnviada] = useState(false)
  const [enviandoSolicitud, setEnviandoSolicitud] = useState(false)

  useEffect(() => {
    setDetalle(null)
    setNivel('obra')
    setUnidadId(null)
    setTemaId(null)
    setSolicitarAbierto(false)
    setSolicitudEnviada(false)
    setNombreSolicitud('')
    if (obraSlug) {
      fetchObraDetalle(obraSlug).then(setDetalle)
    }
  }, [obraSlug])

  function handleObraChange(slug: string, id: number) {
    setObraSlug(slug)
    setObraId(id)
  }

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

  async function handleSolicitarTema() {
    if (!obraId || !nombreSolicitud.trim()) return
    setEnviandoSolicitud(true)
    try {
      await crearSolicitudTema(obraId, nombreSolicitud.trim())
      setSolicitudEnviada(true)
    } finally {
      setEnviandoSolicitud(false)
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
          onChange={(e) => {
            const obra = obras.find((o) => o.slug === e.target.value)
            handleObraChange(e.target.value, obra?.id ?? 0)
          }}
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
              {detalle.temas.length > 0 ? (
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
              ) : (
                <p className={styles.solicitudEnviada}>Esta obra aún no tiene temas registrados.</p>
              )}

              {!solicitudEnviada && (
                solicitarAbierto ? (
                  <div className={styles.solicitudPanel}>
                    <input
                      className={styles.input}
                      type="text"
                      placeholder="Nombre del tema que propones"
                      value={nombreSolicitud}
                      onChange={(e) => setNombreSolicitud(e.target.value)}
                    />
                    <div className={styles.actions}>
                      <button
                        className={`${styles.button} ${styles.cancel}`}
                        onClick={() => setSolicitarAbierto(false)}
                      >
                        Cancelar
                      </button>
                      <button
                        className={`${styles.button} ${styles.confirm}`}
                        onClick={handleSolicitarTema}
                        disabled={!nombreSolicitud.trim() || enviandoSolicitud}
                      >
                        Enviar propuesta
                      </button>
                    </div>
                  </div>
                ) : (
                  <button className={styles.solicitarLink} onClick={() => setSolicitarAbierto(true)}>
                    ¿No encuentras tu tema? Proponlo
                  </button>
                )
              )}

              {solicitudEnviada && (
                <p className={styles.solicitudEnviada}>
                  Propuesta enviada. Aparecerá disponible si se aprueba.
                </p>
              )}
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