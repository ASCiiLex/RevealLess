import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import styles from './PasoPost.module.css'
import BuscadorLocal, { type BuscadorItem } from './BuscadorLocal'
import EditorTexto from './EditorTexto'
import GaleriaEditor, { type CambioEncuadre, type ImagenBorrador } from './GaleriaEditor'
import SelectorParteTema, { type Seleccion } from './SelectorParteTema'
import PersonajesEnfrentados, { type PersonajeElegido } from './PersonajesEnfrentados'
import type { EstadoComparativa } from './Comparativa'
import ReferenciaCruzadaAviso from '../ReferenciaCruzada/ReferenciaCruzadaAviso'
import { MAX_IMAGENES, ZOOM_BASE, disposicionEfectiva } from '../Galeria/GaleriaPost'
import { ApiError } from '../../api/client'
import { fetchObraContextoPublicar, buscarUnidades, type ObraContextoPublicar } from '../../api/suscripciones'
import { crearPost, type DatosPost, type DeteccionCruzada } from '../../api/publicar'

interface Props {
  // null = aún no hay obra elegida: el formulario se muestra desactivado.
  obraSlug: string | null
  temaIdInicial?: number | null
  comparativa: EstadoComparativa
  onPublicado: (postId: number) => void
  onProgresoRequerido: () => void
}

// Decisiones del usuario ante los 409: se acumulan para que un reenvío no pierda las anteriores.
interface Ajustes {
  confirmarSaltoProgreso?: boolean
  obraCruzadaId?: number | null
  fronteraCruzadaId?: number | null
  descartarReferenciaCruzada?: boolean
}

// Origen de la parte de la segunda obra: a mano, autorrellenada o sin equivalente.
type OrigenParteOtra = 'manual' | 'auto' | 'sin-equivalente'

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

const normalizar = (texto: string) => texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim()

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

// Galería, segunda obra y personajes: se añaden a la petición solo si se usan.
function datosExtra(
  imagenes: ImagenBorrador[],
  disposicion: string,
  comparativa: EstadoComparativa,
  parteOtra: Seleccion,
  personajes: PersonajeElegido[],
): Partial<DatosPost> {
  const extra: Partial<DatosPost> = {}
  if (imagenes.length === 1) {
    extra.image = imagenes[0].archivo
  } else if (imagenes.length > 1) {
    extra.imagenes = imagenes.map((i) => i.archivo)
    extra.etiquetas = imagenes.map((i) => i.etiqueta.trim())
    extra.enfoquesX = imagenes.map((i) => i.enfoqueX)
    extra.enfoquesY = imagenes.map((i) => i.enfoqueY)
    extra.zooms = imagenes.map((i) => i.zoom)
    extra.disposicion = disposicionEfectiva(imagenes.length, disposicion)
  }
  if (comparativa.activa) {
    if (comparativa.obra && parteOtra.id) {
      extra.obraCruzadaId = comparativa.obra.id
      extra.fronteraCruzadaId = parteOtra.id
      extra.modoCruce = comparativa.modo
    }
    if (personajes.length >= 2) {
      extra.personajesComparadosIds = personajes.filter((p) => p.id !== null).map((p) => p.id as number)
      extra.personajesPropuestos = personajes.filter((p) => p.id === null).map((p) => p.nombre)
    }
  }
  return extra
}

export default function PasoPost({ obraSlug, temaIdInicial, comparativa, onPublicado, onProgresoRequerido }: Props) {
  const [contexto, setContexto] = useState<ObraContextoPublicar | null>(null)
  const [texto, setTexto] = useState('')
  const [imagenes, setImagenes] = useState<ImagenBorrador[]>([])
  const [disposicion, setDisposicion] = useState('')
  const [emocion, setEmocion] = useState<string | null>(null)
  const [parte, setParte] = useState<Seleccion>(SIN_SELECCION)
  const [tema, setTema] = useState<Seleccion>({ id: temaIdInicial ?? null, label: null })
  // Tema escrito que no existe: se envía como propuesta (solicitud de tema).
  const [temaPropuesto, setTemaPropuesto] = useState<string | null>(null)
  const [parteOtra, setParteOtra] = useState<Seleccion>(SIN_SELECCION)
  const [origenParteOtra, setOrigenParteOtra] = useState<OrigenParteOtra>('auto')
  const [personajes, setPersonajes] = useState<PersonajeElegido[]>([])
  const [frontera, setFrontera] = useState<Seleccion>(SIN_SELECCION)
  const [nuevoProgreso, setNuevoProgreso] = useState<Seleccion>(SIN_SELECCION)
  const [ajustes, setAjustes] = useState<Ajustes>({})
  const [avisoSalto, setAvisoSalto] = useState<string | null>(null)
  const [detecciones, setDetecciones] = useState<DeteccionCruzada[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const origenRef = useRef<OrigenParteOtra>('auto')

  useEffect(() => {
    if (obraSlug) fetchObraContextoPublicar(obraSlug).then(setContexto)
  }, [obraSlug])

  useEffect(() => {
    const inicial = contexto?.temas.find((t) => t.id === temaIdInicial)
    if (inicial) {
      setTema((actual) => (actual.id === inicial.id ? { ...actual, label: inicial.nombre } : actual))
    }
  }, [temaIdInicial, contexto])

  // Al cambiar la segunda obra se descarta lo elegido en ella.
  const otraSlug = comparativa.obra?.slug ?? null
  useEffect(() => {
    setParteOtra(SIN_SELECCION)
    origenRef.current = 'auto'
    setOrigenParteOtra('auto')
    setPersonajes((prev) => prev.filter((p) => !p.deOtraObra))
  }, [otraSlug])

  // Misma escena: la parte de la segunda obra se autorrellena por nombre, salvo si el autor la eligió a mano.
  const mismaEscena = comparativa.activa && comparativa.modo === 'misma_escena'
  useEffect(() => {
    if (!mismaEscena || !otraSlug || !parte.label || origenRef.current === 'manual') return
    let vigente = true
    const nombre = parte.label
    buscarUnidades(otraSlug, nombre).then((items) => {
      if (!vigente || origenRef.current === 'manual') return
      const igual = items.find((i) => normalizar(i.label) === normalizar(nombre))
      if (igual) {
        setParteOtra(igual)
        origenRef.current = 'auto'
        setOrigenParteOtra('auto')
      } else {
        setParteOtra(SIN_SELECCION)
        origenRef.current = 'sin-equivalente'
        setOrigenParteOtra('sin-equivalente')
      }
    })
    return () => {
      vigente = false
    }
  }, [mismaEscena, otraSlug, parte.label])

  // Referencias estables: BuscadorLocal relanza la búsqueda si cambia su prop buscar.
  const buscarUnidadesObra = useCallback(
    (q: string) => (obraSlug ? buscarUnidades(obraSlug, q) : Promise.resolve([])),
    [obraSlug]
  )
  const buscarUnidadesOtra = useCallback(
    (q: string) => (otraSlug ? buscarUnidades(otraSlug, q) : Promise.resolve([])),
    [otraSlug]
  )

  const activo = Boolean(obraSlug && contexto)

  function handleTema(seleccion: Seleccion) {
    setTema(seleccion)
    setTemaPropuesto(null)
  }

  function handleProponerTema(nombre: string | null) {
    setTema(SIN_SELECCION)
    setTemaPropuesto(nombre)
  }

  function handleParteOtra(seleccion: Seleccion) {
    setParteOtra(seleccion)
    // Vaciarla devuelve el control al autorrelleno.
    const origen: OrigenParteOtra = seleccion.id ? 'manual' : 'auto'
    origenRef.current = origen
    setOrigenParteOtra(origen)
  }

  function anadirImagenes(archivos: File[]) {
    const libres = MAX_IMAGENES - imagenes.length
    const nuevas = archivos.slice(0, libres).map((archivo) => ({
      archivo,
      etiqueta: '',
      url: URL.createObjectURL(archivo),
      enfoqueX: 50,
      enfoqueY: 50,
      zoom: ZOOM_BASE,
    }))
    setImagenes([...imagenes, ...nuevas])
  }

  function quitarImagen(indice: number) {
    URL.revokeObjectURL(imagenes[indice].url)
    setImagenes(imagenes.filter((_, i) => i !== indice))
  }

  function cambiarEtiqueta(indice: number, etiqueta: string) {
    setImagenes((prev) => prev.map((img, i) => (i === indice ? { ...img, etiqueta } : img)))
  }

  function cambiarEncuadre(indice: number, cambio: CambioEncuadre) {
    setImagenes((prev) => prev.map((img, i) => (i === indice ? { ...img, ...cambio } : img)))
  }

  const hayParteOTema = Boolean(parte.id || tema.id || temaPropuesto)
  const comparativaIncompleta =
    comparativa.activa && ((comparativa.obra !== null && !parteOtra.id) || personajes.length === 1)

  async function enviar(ajustesEnvio: Ajustes) {
    if (!obraSlug || !hayParteOTema || enviando) return
    setError(null)
    setAvisoSalto(null)
    setEnviando(true)

    try {
      const resultado = await crearPost(obraSlug, {
        text: texto,
        referenciaNarrativaId: parte.id,
        fronteraSpoilerId: frontera.id,
        emocionAutor: emocion,
        temaId: tema.id,
        temaPropuesto: tema.id ? undefined : temaPropuesto ?? undefined,
        nuevoProgresoId: nuevoProgreso.id,
        ...ajustesEnvio,
        // La comparativa explícita prevalece sobre lo elegido en el aviso de detección.
        ...datosExtra(imagenes, disposicion, comparativa, parteOtra, personajes),
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

  const otra = comparativa.activa ? comparativa.obra : null

  function pistaParteOtra(titulo: string) {
    if (!mismaEscena) return 'Solo lo verá quien haya llegado aquí y a la frontera de la obra principal.'
    if (origenParteOtra === 'sin-equivalente' && parte.label) {
      return `No hay una parte llamada «${parte.label}» en ${titulo}: indícala.`
    }
    if (origenParteOtra === 'auto' && parteOtra.id) {
      return 'Rellenada con la parte del mismo nombre. Cámbiala si no coincide.'
    }
    return `Así también lo verán quienes solo lleven ${titulo}.`
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
          <div className={styles.field}>
            <label className={styles.label} htmlFor="parte-tema">¿De qué parte o tema habla?</label>
            <SelectorParteTema
              id="parte-tema"
              obraSlug={obraSlug}
              temas={contexto?.temas ?? []}
              parte={parte}
              tema={tema}
              temaPropuesto={temaPropuesto}
              onParte={setParte}
              onTema={handleTema}
              onProponerTema={handleProponerTema}
            />
            <span className={styles.hint}>
              {temaPropuesto
                ? 'Si el tema ya existe en esta obra se asigna al publicar; si no, se revisará antes de crearlo.'
                : 'Elige una parte, un tema o ambos.'}
            </span>
          </div>

          {otra && (
            <CampoSeleccion
              id="parte-otra"
              etiqueta={
                mismaEscena
                  ? `¿En qué parte de ${otra.titulo} ocurre esta escena?`
                  : `¿De qué parte de ${otra.titulo}?`
              }
              seleccion={parteOtra}
              onChange={handleParteOtra}
              placeholder="Buscar unidad..."
              buscar={buscarUnidadesOtra}
              hint={pistaParteOtra(otra.titulo)}
            />
          )}

          {comparativa.activa && (
            <PersonajesEnfrentados
              obraSlug={obraSlug}
              otraObra={otra}
              valor={personajes}
              onChange={setPersonajes}
            />
          )}

          <div className={styles.field}>
            <label className={styles.label} htmlFor="text">¿Qué quieres contar?</label>
            <EditorTexto
              id="text"
              texto={texto}
              onTextoChange={setTexto}
              emocion={emocion}
              onEmocionChange={setEmocion}
              numImagenes={imagenes.length}
              onAnadirImagenes={anadirImagenes}
            />
            <GaleriaEditor
              imagenes={imagenes}
              disposicion={disposicion}
              onDisposicion={setDisposicion}
              onEtiqueta={cambiarEtiqueta}
              onEncuadre={cambiarEncuadre}
              onQuitar={quitarImagen}
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

          <button
            className={styles.submit}
            type="submit"
            disabled={enviando || !hayParteOTema || comparativaIncompleta}
          >
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