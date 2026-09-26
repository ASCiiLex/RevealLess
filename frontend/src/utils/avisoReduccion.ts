interface UnidadConOrden {
  id: number
  orden_inicio: number
}

interface CambiosNarrativos {
  unidades: UnidadConOrden[]
  referenciaOriginalId: number | null
  referenciaNuevaId: number | null
  fronteraOriginalId: number | null
  fronteraNuevaId: number | null
}

/** Aviso si la edición mueve la referencia o reduce la frontera hacia atrás; null si no. */
export function detectarReduccion({
  unidades,
  referenciaOriginalId,
  referenciaNuevaId,
  fronteraOriginalId,
  fronteraNuevaId,
}: CambiosNarrativos): string | null {
  const orden = new Map(unidades.map((u) => [u.id, u.orden_inicio]))

  function retrocede(originalId: number | null, nuevoId: number | null): boolean {
    if (!originalId || !nuevoId || originalId === nuevoId) return false
    const antes = orden.get(originalId)
    const despues = orden.get(nuevoId)
    return antes !== undefined && despues !== undefined && despues < antes
  }

  const avisos: string[] = []
  if (retrocede(referenciaOriginalId, referenciaNuevaId)) {
    avisos.push('estás moviendo la referencia narrativa hacia atrás')
  }
  if (retrocede(fronteraOriginalId, fronteraNuevaId)) {
    avisos.push('estás reduciendo la frontera de spoiler')
  }

  if (avisos.length === 0) return null
  return `Atención: ${avisos.join(' y ')}. Esto no oculta el contenido a lectores que ya lo hayan visto con los valores anteriores.`
}