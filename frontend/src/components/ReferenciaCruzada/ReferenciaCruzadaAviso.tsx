import { useEffect, useState } from 'react'
import styles from './ReferenciaCruzadaAviso.module.css'
import AvisoIA from '../IA/AvisoIA'
import { fetchObraDetalle } from '../../api/suscripciones'
import { sugerirFrontera, type DeteccionCruzada, type ModoCruce } from '../../api/publicar'
import { normalizar } from '../../utils/texto'

export type { DeteccionCruzada }

interface UnidadOpcion {
  id: number
  etiqueta: string
}

type Propuesta = { origen: 'nombre' } | { origen: 'ia'; certeza: number; fiable: boolean }

interface Props {
  detecciones: DeteccionCruzada[]
  // Frontera de la obra principal: si la otra obra tiene una unidad con el mismo nombre, se propone.
  // Nunca la parte: en «misma escena» quedaría por detrás de lo que revela el texto.
  fronteraNombre?: string | null
  // Sin coincidencia por nombre, la IA propone el punto con el texto y la obra desde la que se publica.
  texto?: string
  obraPrincipalSlug?: string | null
  onConfirmar: (obraCruzadaId: number, fronteraCruzadaId: number, modo: ModoCruce) => void
  onDescartar: () => void
  onCancelar: () => void
}

// «Saga · Arco» → «Arco»: se compara el nombre propio de la unidad.
const nombreBase = (nombre: string) => nombre.split(' · ').pop() ?? nombre

export default function ReferenciaCruzadaAviso({
  detecciones, fronteraNombre, texto, obraPrincipalSlug, onConfirmar, onDescartar, onCancelar,
}: Props) {
  const [obraId, setObraId] = useState(detecciones[0]?.obraId ?? null)
  const [unidades, setUnidades] = useState<UnidadOpcion[]>([])
  const [fronteraId, setFronteraId] = useState<number | null>(null)
  const [propuesta, setPropuesta] = useState<Propuesta | null>(null)
  const [buscandoIA, setBuscandoIA] = useState(false)
  const [modo, setModo] = useState<ModoCruce>('comparativa')

  const detectada = detecciones.find((d) => d.obraId === obraId) ?? detecciones[0]

  useEffect(() => {
    if (!detectada) return
    let vigente = true
    setModo(detectada.mismaHistoria ? 'misma_escena' : 'comparativa')
    setFronteraId(null)
    setPropuesta(null)

    fetchObraDetalle(detectada.obraSlug).then(async (d) => {
      if (!vigente) return
      setUnidades(d.unidades)
      const buscado = fronteraNombre ? normalizar(nombreBase(fronteraNombre)) : null
      const igual = buscado ? d.unidades.find((u) => normalizar(nombreBase(u.etiqueta)) === buscado) : undefined
      if (igual) {
        setFronteraId(igual.id)
        setPropuesta({ origen: 'nombre' })
        return
      }
      if (!texto?.trim() || !obraPrincipalSlug) return
      setBuscandoIA(true)
      try {
        const r = await sugerirFrontera(detectada.obraSlug, texto, null, obraPrincipalSlug)
        if (!vigente || !r.frontera) return
        const sugerida = r.frontera
        // La IA puede elegir una unidad que no esté en el desplegable (un arco): se añade.
        setUnidades((prev) => (prev.some((u) => u.id === sugerida.id) ? prev : [...prev, sugerida]))
        setFronteraId(sugerida.id)
        setPropuesta({ origen: 'ia', certeza: Math.round(r.confianza * 100), fiable: r.fiable })
      } catch {
        // Sin propuesta: el autor elige a mano.
      } finally {
        if (vigente) setBuscandoIA(false)
      }
    })
    return () => {
      vigente = false
    }
  }, [detectada?.obraSlug, detectada?.mismaHistoria, fronteraNombre, texto, obraPrincipalSlug])

  if (!detectada) {
    return null
  }

  const titulo = detectada.obraTitulo
  // La propuesta de la IA no va como pista discreta: la muestra el aviso destacado.
  const pistaPropuesta = buscandoIA
    ? `La IA está buscando el punto equivalente en ${titulo}…`
    : propuesta?.origen === 'nombre'
      ? `Propuesta: la parte con el mismo nombre en ${titulo}. Cámbiala si no coincide.`
      : null

  return (
    <div className={styles.overlay}>
      <div className={styles.modal}>
        <h3 className={styles.title}>Posible referencia a otra obra</h3>
        <p className={styles.text}>
          El texto contiene la palabra "<strong>{detectada.palabra}</strong>", que podría
          referirse a <strong>{titulo}</strong>. Si es así, indica hasta qué
          punto de esa obra hay que haber llegado para leer esto sin spoiler.
        </p>

        {detecciones.length > 1 && (
          <select
            className={styles.select}
            value={obraId ?? ''}
            onChange={(e) => setObraId(Number(e.target.value))}
          >
            {detecciones.map((d) => (
              <option key={d.obraId} value={d.obraId}>{d.obraTitulo}</option>
            ))}
          </select>
        )}

        {detectada.mismaHistoria && (
          <div className={styles.modos} role="radiogroup" aria-label="Quién puede verlo">
            <label className={styles.modo}>
              <input
                type="radio"
                name="modo-cruce-aviso"
                checked={modo === 'misma_escena'}
                onChange={() => setModo('misma_escena')}
              />
              <span>
                <span className={styles.modoTitulo}>Misma escena en otro formato</span>
                <span className={styles.hint}>Basta con haber llegado en una de las dos obras.</span>
              </span>
            </label>
            <label className={styles.modo}>
              <input
                type="radio"
                name="modo-cruce-aviso"
                checked={modo === 'comparativa'}
                onChange={() => setModo('comparativa')}
              />
              <span>
                <span className={styles.modoTitulo}>Comparativa</span>
                <span className={styles.hint}>Hay que haber llegado en las dos obras.</span>
              </span>
            </label>
          </div>
        )}

        <select
          className={styles.select}
          value={fronteraId ?? ''}
          disabled={buscandoIA}
          onChange={(e) => {
            setFronteraId(Number(e.target.value) || null)
            setPropuesta(null)
          }}
        >
          <option value="">Elige el punto de {titulo}</option>
          {unidades.map((u) => (
            <option key={u.id} value={u.id}>{u.etiqueta}</option>
          ))}
        </select>

        {pistaPropuesta && <p className={styles.hint}>{pistaPropuesta}</p>}

        {!buscandoIA && propuesta?.origen === 'ia' && (
          <div className={styles.avisoIA}>
            <AvisoIA certeza={propuesta.certeza} fiable={propuesta.fiable} accion="confirmar" superficie="clara" />
          </div>
        )}

        <div className={styles.actions}>
          <button
            className={styles.confirmar}
            disabled={!fronteraId || buscandoIA}
            onClick={() => fronteraId && onConfirmar(detectada.obraId, fronteraId, modo)}
          >
            Sí, es de ahí — confirmar
          </button>
          <button className={styles.descartar} onClick={onDescartar}>
            No, es coincidencia — publicar igual
          </button>
          <button className={styles.cancelar} onClick={onCancelar}>
            Cancelar
          </button>
        </div>
      </div>
    </div>
  )
}