import { useCallback, useEffect, useState, type FormEvent } from 'react'
import styles from './PasoPost.module.css'
import CampoSeleccion from './CampoSeleccion'
import CampoVideo, { enlaceYouTubeValido } from './CampoVideo'
import EditorTexto from './EditorTexto'
import GaleriaEditor from './GaleriaEditor'
import SelectorParteTema, { type Seleccion } from './SelectorParteTema'
import PersonajesEnfrentados, { type PersonajeElegido } from './PersonajesEnfrentados'
import type { EstadoComparativa } from './Comparativa'
import {
  SIN_SELECCION, comparativaIncompleta, datosExtra, hayPersonajeDeOtraObra, pistaFrontera, pistaParte,
} from './pasoPostDatos'
import { useContextoObra } from './useContextoObra'
import { useEnvioPost } from './useEnvioPost'
import { useGaleriaBorrador } from './useGaleriaBorrador'
import { useParteOtra } from './useParteOtra'
import { useSugerenciaIA } from './useSugerenciaIA'
import AvisoIA from '../IA/AvisoIA'
import ReferenciaCruzadaAviso from '../ReferenciaCruzada/ReferenciaCruzadaAviso'
import { buscarUnidades } from '../../api/suscripciones'

interface Props {
  // null = aún no hay obra elegida: el formulario se muestra desactivado.
  obraSlug: string | null
  temaIdInicial?: number | null
  comparativa: EstadoComparativa
  onPublicado: (postId: number) => void
  onProgresoRequerido: () => void
}

const PISTA_VIDEO_BLOQUEADO = 'Quita las imágenes para añadir un vídeo: un post lleva una cosa u otra.'
const ERROR_CONTEXTO = 'No se pudo cargar la obra. Recarga la página para publicar.'

export default function PasoPost({ obraSlug, temaIdInicial, comparativa, onPublicado, onProgresoRequerido }: Props) {
  const [texto, setTexto] = useState('')
  const [emocion, setEmocion] = useState<string | null>(null)
  const [videoUrl, setVideoUrl] = useState('')
  const [parte, setParte] = useState<Seleccion>(SIN_SELECCION)
  const [tema, setTema] = useState<Seleccion>({ id: temaIdInicial ?? null, label: null })
  // Tema escrito que no existe: se envía como propuesta (solicitud de tema).
  const [temaPropuesto, setTemaPropuesto] = useState<string | null>(null)
  const [personajes, setPersonajes] = useState<PersonajeElegido[]>([])
  const [frontera, setFrontera] = useState<Seleccion>(SIN_SELECCION)
  const [nuevoProgreso, setNuevoProgreso] = useState<Seleccion>(SIN_SELECCION)

  const videoLimpio = videoUrl.trim()
  const videoValido = enlaceYouTubeValido(videoUrl)

  const { contexto, fallo: falloContexto } = useContextoObra(obraSlug)
  const galeria = useGaleriaBorrador()
  const { parteOtra, otraSlug, elegir: elegirParteOtra, pista: pistaParteOtra, mismaEscena } =
    useParteOtra(comparativa, parte.label)
  const ia = useSugerenciaIA({
    obraSlug,
    texto,
    parte,
    frontera,
    video: videoValido && videoLimpio ? videoLimpio : null,
    onParte: setParte,
    onFrontera: setFrontera,
  })

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
  const hayImagenes = galeria.imagenes.length > 0
  // Basta con parte, tema o frontera: la parte es contexto, la visibilidad la decide la frontera.
  const hayAncla = Boolean(parte.id || tema.id || temaPropuesto || frontera.id)
  // Con un personaje de la otra obra, su parte es opcional: la frontera cruzada sale de su primera aparición.
  const conPersonajeDeOtra = hayPersonajeDeOtraObra(personajes)
  const incompleta = comparativaIncompleta(comparativa, parteOtra, personajes)
  const otra = comparativa.activa ? comparativa.obra : null
  const parteOtraOpcional = conPersonajeDeOtra && !parteOtra.id

  const envio = useEnvioPost({
    obraSlug,
    listo: hayAncla,
    construir: (ajustes) => ({
      text: texto,
      referenciaNarrativaId: parte.id,
      fronteraSpoilerId: frontera.id,
      fronteraSugeridaIaId: ia.sugerencia?.id ?? null,
      iaConfianza: ia.sugerencia?.confianza ?? null,
      emocionAutor: emocion,
      temaId: tema.id,
      temaPropuesto: tema.id ? undefined : temaPropuesto ?? undefined,
      nuevoProgresoId: nuevoProgreso.id,
      videoUrl: videoLimpio || undefined,
      ...ajustes,
      // La comparativa explícita prevalece sobre lo elegido en el aviso de detección.
      ...datosExtra(galeria.imagenes, galeria.disposicion, comparativa, parteOtra, personajes),
    }),
    onPublicado,
    onProgresoRequerido,
  })

  function handleTema(seleccion: Seleccion) {
    setTema(seleccion)
    setTemaPropuesto(null)
  }

  function handleProponerTema(nombre: string | null) {
    setTema(SIN_SELECCION)
    setTemaPropuesto(nombre)
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    envio.publicar()
  }

  return (
    <>
      <form className={styles.form} onSubmit={handleSubmit}>
        {falloContexto && <p className={styles.error}>{ERROR_CONTEXTO}</p>}
        {envio.error && <p className={styles.error}>{envio.error}</p>}
        {envio.avisoSalto && (
          <p className={styles.error}>
            {envio.avisoSalto}{' '}
            <button type="button" onClick={() => envio.enviarCon({ confirmarSaltoProgreso: true })}>
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
              imagenesBloqueadas={Boolean(videoLimpio)}
            />
            <GaleriaEditor
              imagenes={galeria.imagenes}
              disposicion={galeria.disposicion}
              onDisposicion={galeria.setDisposicion}
              onEtiqueta={galeria.cambiarEtiqueta}
              onEncuadre={galeria.cambiarEncuadre}
              onQuitar={galeria.quitar}
            />
            <CampoVideo
              id="video"
              valor={videoUrl}
              onChange={setVideoUrl}
              deshabilitado={hayImagenes}
              pista={hayImagenes ? PISTA_VIDEO_BLOQUEADO : undefined}
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
            <span className={styles.hint}>{pistaParte(temaPropuesto, ia.parteVigente)}</span>
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
              onClick={ia.pedir}
              disabled={ia.sugiriendo || !texto.trim()}
            >
              {ia.sugiriendo ? 'Consultando a la IA…' : 'Sugerir frontera con IA'}
            </button>
            {ia.aviso && <span className={styles.hint}>{ia.aviso}</span>}
          </div>

          <CampoSeleccion
            id="frontera"
            etiqueta="Frontera de spoiler"
            seleccion={frontera}
            onChange={setFrontera}
            placeholder="Buscar unidad..."
            emptyLabel="Dejar que la IA la estime al publicar"
            buscar={buscarFronterasObra}
            hint={pistaFrontera(ia.vigente, Boolean(frontera.id))}
          />

          {ia.vigente && <AvisoIA certeza={ia.certeza} fiable={ia.fiable} accion="publicar" />}

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
            disabled={envio.enviando || !hayAncla || incompleta || !videoValido}
          >
            {envio.enviando ? 'Publicando...' : 'Publicar'}
          </button>
        </fieldset>
      </form>

      {envio.detecciones && (
        <ReferenciaCruzadaAviso
          detecciones={envio.detecciones}
          fronteraNombre={frontera.label}
          texto={texto}
          obraPrincipalSlug={obraSlug}
          onConfirmar={(obraCruzadaId, fronteraCruzadaId, modoCruce) =>
            envio.enviarCon({ obraCruzadaId, fronteraCruzadaId, modoCruce })
          }
          onDescartar={() => envio.enviarCon({ descartarReferenciaCruzada: true })}
          onCancelar={envio.cerrarDetecciones}
        />
      )}
    </>
  )
}