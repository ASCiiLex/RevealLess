import { useEffect, useState } from 'react'
import { fetchObraContextoPublicar, type ObraContextoPublicar } from '../../api/suscripciones'

// Temas de la obra para publicar. Una respuesta de otra obra se descarta; un fallo se señala.
export function useContextoObra(obraSlug: string | null) {
  const [contexto, setContexto] = useState<ObraContextoPublicar | null>(null)
  const [fallo, setFallo] = useState(false)

  useEffect(() => {
    setContexto(null)
    setFallo(false)
    if (!obraSlug) return
    let vigente = true
    fetchObraContextoPublicar(obraSlug)
      .then((datos) => {
        if (vigente) setContexto(datos)
      })
      .catch(() => {
        if (vigente) setFallo(true)
      })
    return () => {
      vigente = false
    }
  }, [obraSlug])

  return { contexto, fallo }
}