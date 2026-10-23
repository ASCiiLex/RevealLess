import { useState } from 'react'
import { sugerirFrontera } from '../../api/publicar'
import type { Seleccion } from './SelectorParteTema'

const AVISO_FALLO_IA = 'No se pudo consultar a la IA: elige la frontera o se usará tu progreso actual.'

interface SugerenciaVista {
  id: number
  confianza: number
  fiable: boolean
}

interface Entrada {
  obraSlug: string | null
  texto: string
  parte: Seleccion
  frontera: Seleccion
  // Enlace de YouTube ya validado, o null.
  video: string | null
  onParte: (seleccion: Seleccion) => void
  onFrontera: (seleccion: Seleccion) => void
}

// Propuesta de frontera (y de parte, si falta) antes de publicar. Rellena los campos; el autor decide.
export function useSugerenciaIA({ obraSlug, texto, parte, frontera, video, onParte, onFrontera }: Entrada) {
  const [sugerencia, setSugerencia] = useState<SugerenciaVista | null>(null)
  const [sugiriendo, setSugiriendo] = useState(false)
  const [aviso, setAviso] = useState<string | null>(null)
  // Id de la parte rellenada por la IA: mientras siga elegida, se avisa de que hay que comprobarla.
  const [parteDeIA, setParteDeIA] = useState<number | null>(null)

  async function pedir() {
    if (!obraSlug || !texto.trim() || sugiriendo) return
    setSugiriendo(true)
    setAviso(null)
    try {
      const resultado = await sugerirFrontera(obraSlug, texto, parte.id, null, video)
      if (!resultado.frontera) {
        setSugerencia(null)
        setAviso(AVISO_FALLO_IA)
        return
      }
      // La parte solo se propone si el autor no la había elegido.
      if (resultado.parte && !parte.id) {
        onParte({ id: resultado.parte.id, label: resultado.parte.etiqueta })
        setParteDeIA(resultado.parte.id)
      }
      onFrontera({ id: resultado.frontera.id, label: resultado.frontera.etiqueta })
      setSugerencia({ id: resultado.frontera.id, confianza: resultado.confianza, fiable: resultado.fiable })
    } catch {
      setAviso(AVISO_FALLO_IA)
    } finally {
      setSugiriendo(false)
    }
  }

  // Vigente mientras el autor no cambie la frontera propuesta.
  const vigente = sugerencia !== null && frontera.id === sugerencia.id

  return {
    sugerencia,
    sugiriendo,
    aviso,
    pedir,
    vigente,
    // «Certeza»: lo seguro que está el modelo del punto elegido, no lo protegido que está el post.
    certeza: sugerencia ? Math.round(sugerencia.confianza * 100) : 0,
    fiable: sugerencia?.fiable ?? false,
    parteVigente: parteDeIA !== null && parte.id === parteDeIA,
  }
}