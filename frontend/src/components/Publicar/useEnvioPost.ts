import { useState } from 'react'
import { crearPost, type DatosPost, type DeteccionCruzada, type ModoCruce } from '../../api/publicar'
import { mensajeDeError } from './pasoPostDatos'

// Decisiones del usuario ante los 409: se acumulan para que un reenvío no pierda las anteriores.
export interface Ajustes {
  confirmarSaltoProgreso?: boolean
  obraCruzadaId?: number | null
  fronteraCruzadaId?: number | null
  modoCruce?: ModoCruce
  descartarReferenciaCruzada?: boolean
}

interface Opciones {
  obraSlug: string | null
  // Hay parte, tema o frontera: sin ancla no se envía.
  listo: boolean
  // Datos del formulario con las decisiones acumuladas, en el momento del envío.
  construir: (ajustes: Ajustes) => DatosPost
  onPublicado: (postId: number) => void
  onProgresoRequerido: () => void
}

// Envío del post: cada 409 se resuelve con una decisión del autor y se reenvía con todas las anteriores.
export function useEnvioPost({ obraSlug, listo, construir, onPublicado, onProgresoRequerido }: Opciones) {
  const [ajustes, setAjustes] = useState<Ajustes>({})
  const [avisoSalto, setAvisoSalto] = useState<string | null>(null)
  const [detecciones, setDetecciones] = useState<DeteccionCruzada[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function enviar(ajustesEnvio: Ajustes) {
    if (!obraSlug || !listo || enviando) return
    setError(null)
    setAvisoSalto(null)
    setEnviando(true)

    try {
      const resultado = await crearPost(obraSlug, construir(ajustesEnvio))

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

  return {
    avisoSalto,
    detecciones,
    error,
    enviando,
    publicar: () => enviar(ajustes),
    enviarCon,
    cerrarDetecciones: () => setDetecciones(null),
  }
}