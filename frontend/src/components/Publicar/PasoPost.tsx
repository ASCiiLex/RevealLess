import { useCallback, useEffect, useState, type FormEvent } from 'react'
import styles from './PasoPost.module.css'
import CampoSeleccion from './CampoSeleccion'
import EditorTexto from './EditorTexto'
import GaleriaEditor from './GaleriaEditor'
import SelectorParteTema, { type Seleccion } from './SelectorParteTema'
import PersonajesEnfrentados, { type PersonajeElegido } from './PersonajesEnfrentados'
import type { EstadoComparativa } from './Comparativa'
import { SIN_SELECCION, datosExtra, hayPersonajeDeOtraObra, mensajeDeError } from './pasoPostDatos'
import { useGaleriaBorrador } from './useGaleriaBorrador'
import { useParteOtra } from './useParteOtra'
import AvisoIA from '../IA/AvisoIA'
import ReferenciaCruzadaAviso from '../ReferenciaCruzada/ReferenciaCruzadaAviso'
import { fetchObraContextoPublicar, buscarUnidades, type ObraContextoPublicar } from '../../api/suscripciones'
import { crearPost, sugerirFrontera, type DeteccionCruzada, type ModoCruce } from '../../api/publicar'

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
  modoCruce?: ModoCruce
  descartarReferenciaCruzada?: boolean
}

interface SugerenciaVista {
  id: number
  confianza: number
  fiable: boolean
}

const AVISO_FALLO_IA = 'No se pudo consultar a la IA: elige la frontera o se usará tu progreso actual.'

export default function PasoPost({ obraSlug, temaIdInicial, comparativa, onPublicado, onProgresoRequerido }: Props) {
  const [contexto, setContexto] = useState<ObraContextoPublicar | null>(null)
  const [texto, setTexto] = useState('')
  const [emocion, setEmocion] = useState<string | null>(null)
  const [parte, setParte] = useState<Seleccion>(SIN_SELECCION)
  // Id de la parte rellenada por la IA: mientras siga elegida, se avisa de que hay que comprobarla.
  const [parteDeIA, setParteDeIA] = useState<number | null>(null)
  const [tema, setTema] = useState<Seleccion>({ id: temaIdInicial ?? null, label: null })
  // Tema escrito que no existe: se envía como propuesta (solicitud de tema).
  const [temaPropuesto, setTemaPropuesto] = useState<string | null>(null)
  const [personajes, setPersonajes] = useState<PersonajeElegido[]>([])
  const [frontera, setFrontera] = useState<Seleccion>(SIN_SELECCION)
  const [sugerencia, setSugerencia] = useState<SugerenciaVista | null>(null)
  const [sugiriendo, setSugiriendo] = useState(false)
  const [avisoIA, setAvisoIA] = useState<string | null>(null)
  const [nuevoProgreso, setNuevoProgreso] = useState<Seleccion>(SIN_SELECCION)
  const [ajustes, setAjustes] = useState<Ajustes>({})
  const [avisoSalto, setAvisoSalto] = useState<string | null>(null)
  const [detecciones, setDetecciones] = useState<DeteccionCruzada[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  const galeria = useGaleriaBorrador()
  const { parteOtra, otraSlug, elegir: elegirParteOtra, pista: pistaParteOtra, mismaEscena } =
    useParteOtra(comparativa, parte.label)

  useEffect(() => {
    if (obraSlug) fetchObraContextoPublicar(obraSlug).then(setContexto)
  }, [obraSlug])

  useEffect(() => {
    const inicial = contexto?.temas.find((t) => t.id === temaIdInicial)
    if (inicial) {
      setTema((actual) => (actual.id === inicial.id ? { ...actual, label: inicial.nombre } : actual))
    }
  }, [temaIdInicial, contexto])

  // Al cambiar la segunda obra se descartan sus personajes.
  useEffect(() => {
    setPersonajes((prev) => prev.filter((p) => !p.deOtraObra))
  }, [otraSlug])

  // Referencias estables: BuscadorLocal relanza la búsqueda si cambia su prop buscar.
  const buscarUnidadesObra = useCallback(
    (q: string) => (obraSlug ? buscarUnidades(obraSlug, q) : Promise.resolve([])),
    [obraSlug]
  )
  // Fronteras (propia y de la otra obra): sin los previos ya estrenados.
  const buscarFronterasObra = useCallback(
    (q: string) => (obraSlug ? buscarUnidades(obraSlug, q, true) : Promise.resolve([])),
    [obraSlug]
  )
  const buscarFronterasOtra = useCallback(
    (q: string) => (otraSlug ? buscarUnidades(otraSlug, q, true) : Promise.resolve([])),
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

  async function pedirSugerencia() {
    if (!obraSlug || !texto.trim() || sugiriendo) return
    setSugiriendo(true)
    setAvisoIA(null)
    try {
      const resultado = await sugerirFrontera(obraSlug, texto, parte.id)
      if (!resultado.frontera) {
        setSugerencia(null)
        setAvisoIA(AVISO_FALLO_IA)
        return
      }
      // La parte solo se propone si el autor no la había elegido.
      if (resultado.parte && !parte.id) {
        setParte({ id: resultado.parte.id, label: resultado.parte.etiqueta })
        setParteDeIA(resultado.parte.id)
      }
      setFrontera({ id: resultado.frontera.id, label: resultado.frontera.etiqueta })
      setSugerencia({ id: resultado.frontera.id, confianza: resultado.confianza, fiable: resultado.fiable })
    } catch {
      setAvisoIA(AVISO_FALLO_IA)
    } finally {
      setSugiriendo(false)
    }
  }

  const parteSugeridaVigente = parteDeIA !== null && parte.id === parteDeIA
  const pistaParte = temaPropuesto
    ? 'Si el tema ya existe en esta obra se asigna al publicar; si no, se revisará antes de crearlo.'
    : parteSugeridaVigente
      ? 'Parte propuesta por la IA: compruébala. Solo indica de qué habla; quién lo ve lo decide la frontera.'
      : 'Opcional si indicas la frontera. Elegirla antes de sugerir ayuda a la IA a acertar.'

  // «Certeza»: lo seguro que está el modelo del punto elegido, no lo protegido que está el post.
  const sugerenciaVigente = sugerencia !== null && frontera.id === sugerencia.id
  const certeza = sugerencia ? Math.round(sugerencia.confianza * 100) : 0
  // Con propuesta de la IA vigente, la pista la sustituye el aviso destacado.
  const pistaFrontera = sugerenciaVigente
    ? ''
    : frontera.id
      ? 'Frontera elegida por ti. Nunca quedará por debajo de la parte de la que hablas.'
      : 'Si no indicas ninguna, la IA la estimará al publicar; si no puede, se usa tu progreso actual.'

  // Basta con parte, tema o frontera: la parte es contexto, la visibilidad la decide la frontera.
  const hayAncla = Boolean(parte.id || tema.id || temaPropuesto || frontera.id)
  // Con un personaje de la otra obra, su parte es opcional: la frontera cruzada sale de su primera aparición.
  const conPersonajeDeOtra = hayPersonajeDeOtraObra(personajes)
  const comparativaIncompleta =
    comparativa.activa &&
    ((comparativa.obra !== null && !parteOtra.id && !conPersonajeDeOtra) || personajes.length === 1)

  async function enviar(ajustesEnvio: Ajustes) {
    if (!obraSlug || !hayAncla || enviando) return
    setError(null)
    setAvisoSalto(null)
    setEnviando(true)

    try {
      const resultado = await crearPost(obraSlug, {
        text: texto,
        referenciaNarrativaId: parte.id,
        fronteraSpoilerId: frontera.id,
        fronteraSugeridaIaId: sugerencia?.id ?? null,
        iaConfianza: sugerencia?.confianza ?? null,
        emocionAutor: emocion,
        temaId: tema.id,
        temaPropuesto: tema.id ? undefined : temaPropuesto ?? undefined,
        nuevoProgresoId: nuevoProgreso.id,
        ...ajustesEnvio,
        // La comparativa explícita prevalece sobre lo elegido en el aviso de detección.
        ...datosExtra(galeria.imagenes, galeria.disposicion, comparativa, parteOtra, personajes),
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
  const parteOtraOpcional = conPersonajeDeOtra && !parteOtra.id

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
              numImagenes={galeria.imagenes.length}
              onAnadirImagenes={galeria.anadir}
            />
            <GaleriaEditor
              imagenes={galeria.imagenes}
              disposicion={galeria.disposicion}
              onDisposicion={galeria.setDisposicion}
              onEtiqueta={galeria.cambiarEtiqueta}
              onEncuadre={galeria.cambiarEncuadre}
              onQuitar={galeria.quitar}
            />
          </div>

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
            <span className={styles.hint}>{pistaParte}</span>
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
              onChange={elegirParteOtra}
              placeholder="Buscar unidad..."
              emptyLabel={conPersonajeDeOtra ? 'Sin parte concreta' : undefined}
              buscar={buscarFronterasOtra}
              hint={
                parteOtraOpcional
                  ? `Opcional: sin parte, lo verá quien ya conozca a sus personajes en ${otra.titulo}.`
                  : pistaParteOtra(otra.titulo)
              }
            />
          )}

          <div className={styles.filaIA}>
            <button
              type="button"
              className={styles.sugerir}
              onClick={pedirSugerencia}
              disabled={sugiriendo || !texto.trim()}
            >
              {sugiriendo ? 'Consultando a la IA…' : 'Sugerir frontera con IA'}
            </button>
            {avisoIA && <span className={styles.hint}>{avisoIA}</span>}
          </div>

          <CampoSeleccion
            id="frontera"
            etiqueta="Frontera de spoiler"
            seleccion={frontera}
            onChange={setFrontera}
            placeholder="Buscar unidad..."
            emptyLabel="Dejar que la IA la estime al publicar"
            buscar={buscarFronterasObra}
            hint={pistaFrontera}
          />

          {sugerenciaVigente && (
            <AvisoIA certeza={certeza} fiable={sugerencia.fiable} accion="publicar" />
          )}

          <CampoSeleccion
            id="nuevo-progreso"
            etiqueta="Actualizar mi progreso a (opcional)"
            seleccion={nuevoProgreso}
            onChange={setNuevoProgreso}
            placeholder="Buscar unidad..."
            emptyLabel="No actualizar"
            buscar={buscarUnidadesObra}
          />

          <button
            className={styles.submit}
            type="submit"
            disabled={enviando || !hayAncla || comparativaIncompleta}
          >
            {enviando ? 'Publicando...' : 'Publicar'}
          </button>
        </fieldset>
      </form>

      {detecciones && (
        <ReferenciaCruzadaAviso
          detecciones={detecciones}
          fronteraNombre={frontera.label}
          texto={texto}
          obraPrincipalSlug={obraSlug}
          onConfirmar={(obraCruzadaId, fronteraCruzadaId, modoCruce) =>
            enviarCon({ obraCruzadaId, fronteraCruzadaId, modoCruce })
          }
          onDescartar={() => enviarCon({ descartarReferenciaCruzada: true })}
          onCancelar={() => setDetecciones(null)}
        />
      )}
    </>
  )
}