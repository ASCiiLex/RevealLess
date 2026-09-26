import { useState } from 'react'

/** Aviso que detiene el guardado hasta que el usuario lo acepta; se rearma al cambiar los datos. */
export function useAvisoConfirmable() {
  const [aviso, setAviso] = useState<string | null>(null)
  const [confirmado, setConfirmado] = useState(false)

  function bloquea(nuevoAviso: string | null): boolean {
    if (confirmado || !nuevoAviso) return false
    setAviso(nuevoAviso)
    return true
  }

  function confirmar() {
    setConfirmado(true)
    setAviso(null)
  }

  function reiniciar() {
    setConfirmado(false)
  }

  return { aviso, bloquea, confirmar, reiniciar }
}