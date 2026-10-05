import { useCallback, useEffect, useState, type FormEvent } from 'react'
import styles from './PasoPost.module.css'
import BuscadorLocal, { type BuscadorItem } from './BuscadorLocal'
import EditorTexto from './EditorTexto'
import ReferenciaCruzadaAviso from '../ReferenciaCruzada/ReferenciaCruzadaAviso'
import { ApiError } from '../../api/client'
import { fetchObraContextoPublicar, buscarUnidades, type ObraContextoPublicar } from '../../api/suscripciones'
import { crearPost, type DeteccionCruzada } from '../../api/publicar'

interface Props {
  // null = aún no hay obra elegida: el formulario se muestra desactivado.
  obraSlug: string | null
  temaIdInicial?: number | null
  onPublicado: (postId: number) => void
  onProgresoRequerido: () => void
}

interface Seleccion {
  id: number | null
  label: string | null
}

// Decisiones del usuario ante los 409: se acumulan para que un reenvío no pierda las anteriores.
interface Ajustes {
  confirmarSaltoProgreso?: boolean
  obraCruzadaId?: number | null
  fronteraCruzadaId?: number | null
  descartarReferenciaCruzada?: boolean
}

const SIN_SELECCION: Seleccion = { id: null, label: null }
const ERROR_GENERICO = 'No se pudo publicar. Revisa los datos e inténtalo de nuevo.'

function mensajeDeError(err: unknown): string {
  const cuerpo = err instanceof ApiError ? err.detail : null
  const detalle = (cuerpo as { detail?: unknown } | null)?.detail ?? cuerpo
  if (typeof detalle === 'string') return detalle
  if (detalle && typeof detalle === 'object') {
    const primero = Object.values(detalle)[0]
    if (Array.isArray(primero) && typeof primero[0] === 'string') return primero[0]
  }
  return ERROR_GENERICO
}

interface CampoSeleccionProps {
  id: string
  etiqueta: string
  seleccion: Seleccion
  onChange: (seleccion: Seleccion) => void
  placeholder: string
  emptyLabel?: string
  buscar: (q: string) => Promise<BuscadorItem[]>
  hint?: string
}

function CampoSeleccion({ id, etiqueta, seleccion, onChange, placeholder, emptyLabel, buscar, hint }: CampoSeleccionProps) {
  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor={id}>{etiqueta}</label>
      <BuscadorLocal
        id={id}
        value={seleccion.id}
        valueLabel={seleccion.label}
        onChange={(nuevoId, label) => onChange({ id: nuevoId, label })}
        placeholder={placeholder}
        emptyLabel={emptyLabel}
        buscar={buscar}
      />
      {hint && <span className={styles.hint}>{hint}</span>}
    </div>
  )
}

export default function PasoPost({ obraSlug, temaIdInicial, onPublicado, onProgresoRequerido }: Props) {
  const [contexto, setContexto] = useState<ObraContextoPublicar | null>(null)
  const [texto, setTexto] = useState('')
  const [imagen, setImagen] = useState<File | null>(null)
  const [emocion, setEmocion] = useState<string | null>(null)
  const [referencia, setReferencia] = useState<Seleccion>(SIN_SELECCION)
  const [frontera, setFrontera] = useState<Seleccion>(SIN_SELECCION)
  const [nuevoProgreso, setNuevoProgreso] = useState<Seleccion>(SIN_SELECCION)
  const [tema, setTema] = useState<Seleccion>({ id: temaIdInicial ?? null, label: null })
  const [temaPropuesto, setTemaPropuesto] = useState('')
  const [ajustes, setAjustes] = useState<Ajustes>({})
  const [avisoSalto, setAvisoSalto] = useState<string | null>(null)
  const [detecciones, setDetecciones] = useState<DeteccionCruzada[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    if (obraSlug) fetchObraContextoPublicar(obraSlug).then(setContexto)
  }, [obraSlug])

  useEffect(() => {
    const inicial = contexto?.temas.find((t) => t.id === temaIdInicial)
    if (inicial) {
      setTema((actual) => (actual.id === inicial.id ? { ...actual, label: inicial.nombre } : actual))
    }
  }, [temaIdInicial, contexto])

  // Referencias estables: BuscadorLocal relanza la búsqueda si cambia su prop buscar.
  const buscarUnidadesObra = useCallback(
    (q: string) => (obraSlug ? buscarUnidades(obraSlug, q) : Promise.resolve([])),
    [obraSlug]
  )

  const buscarTemas = useCallback(
    (q: string) => Promise.resolve(
      (contexto?.temas ?? [])
        .filter((t) => t.nombre.toLowerCase().includes(q.toLowerCase()))
        .map((t) => ({ id: t.id, label: t.nombre }))
    ),
    [contexto]
  )

  const activo = Boolean(obraSlug && contexto)

  async function enviar(ajustesEnvio: Ajustes) {
    if (!obraSlug || !referencia.id || enviando) return
    setError(null)
    setAvisoSalto(null)
    setEnviando(true)

    try {
      const resultado = await crearPost(obraSlug, {
        text: texto,
        image: imagen,
        referenciaNarrativaId: referencia.id,
        fronteraSpoilerId: frontera.id,
        emocionAutor: emocion,
        temaId: tema.id,
        // Solo cuenta si no se eligió un tema existente.
        temaPropuesto: tema.id ? undefined : temaPropuesto.trim() || undefined,
        nuevoProgresoId: nuevoProgreso.id,
        ...ajustesEnvio,
      })

      if ('progresoRequerido' in resultado) {
        onProgresoRequerido()
      } else if ('requiereConfirmacion' in resultado) {
        setAvisoSalto(resultado.detail)
      } else if ('referenciaCruzadaDetectada' in resultado) {
        setDetecciones(resultado.detecciones)
      } else {
        onPublicado(resultado.id)
      }
    } catch (err) {
      setError(mensajeDeError(err))
    } finally {
      setEnviando(false)
    }
  }

  function enviarCon(nuevos: Ajustes) {
    const combinados = { ...ajustes, ...nuevos }
    setAjustes(combinados)
    setDetecciones(null)
    enviar(combinados)
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    enviar(ajustes)
  }

  return (
    <>
      <form className={styles.form} onSubmit={handleSubmit}>
        {error && <p className={styles.error}>{error}</p>}
        {avisoSalto && (
          <p className={styles.error}>
            {avisoSalto}{' '}
            <button type="button" onClick={() => enviarCon({ confirmarSaltoProgreso: true })}>
              Confirmar y publicar
            </button>
          </p>
        )}

        {/* fieldset disabled desactiva de golpe todos los controles hasta que haya obra. */}
        <fieldset className={styles.campos} disabled={!activo}>
          <CampoSeleccion
            id="referencia"
            etiqueta="¿De qué parte habla?"
            seleccion={referencia}
            onChange={setReferencia}
            placeholder="Elige una unidad"
            buscar={buscarUnidadesObra}
          />

          <CampoSeleccion
            id="tema"
            etiqueta="Tema transversal (opcional)"
            seleccion={tema}
            onChange={setTema}
            placeholder="Buscar tema..."
            emptyLabel="Ninguno"
            buscar={buscarTemas}
          />

          {!tema.id && (
            <div className={styles.field}>
              <label className={styles.label} htmlFor="tema-propuesto">¿No está? Propón un tema nuevo (opcional)</label>
              <input
                id="tema-propuesto"
                className={styles.input}
                type="text"
                maxLength={150}
                value={temaPropuesto}
                onChange={(e) => setTemaPropuesto(e.target.value)}
                placeholder="Ej.: Frutas del diablo"
              />
              <span className={styles.hint}>
                Si ya existe en esta obra se asigna al momento; si no, se revisará antes de crearlo.
              </span>
            </div>
          )}

          <div className={styles.field}>
            <label className={styles.label} htmlFor="text">¿Qué quieres contar?</label>
            <EditorTexto
              id="text"
              texto={texto}
              onTextoChange={setTexto}
              emocion={emocion}
              onEmocionChange={setEmocion}
              imagen={imagen}
              onImagenChange={setImagen}
            />
          </div>

          <CampoSeleccion
            id="nuevo-progreso"
            etiqueta="Actualizar mi progreso a (opcional)"
            seleccion={nuevoProgreso}
            onChange={setNuevoProgreso}
            placeholder="Buscar unidad..."
            emptyLabel="No actualizar"
            buscar={buscarUnidadesObra}
          />

          <CampoSeleccion
            id="frontera"
            etiqueta="Frontera de spoiler (opcional)"
            seleccion={frontera}
            onChange={setFrontera}
            placeholder="Buscar unidad..."
            emptyLabel="Dejar que la IA sugiera (o usar tu progreso actual)"
            buscar={buscarUnidadesObra}
            hint="Si no se indica, se intenta clasificar automáticamente; si no es posible, se usa tu progreso actual."
          />

          <button className={styles.submit} type="submit" disabled={enviando || !referencia.id}>
            {enviando ? 'Publicando...' : 'Publicar'}
          </button>
        </fieldset>
      </form>

      {detecciones && (
        <ReferenciaCruzadaAviso
          detecciones={detecciones}
          onConfirmar={(obraCruzadaId, fronteraCruzadaId) => enviarCon({ obraCruzadaId, fronteraCruzadaId })}
          onDescartar={() => enviarCon({ descartarReferenciaCruzada: true })}
          onCancelar={() => setDetecciones(null)}
        />
      )}
    </>
  )
}