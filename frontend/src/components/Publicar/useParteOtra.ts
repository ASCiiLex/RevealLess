import { useEffect, useRef, useState } from 'react'
import { buscarUnidades } from '../../api/suscripciones'
import type { EstadoComparativa } from './Comparativa'
import { SIN_SELECCION } from './pasoPostDatos'
import type { Seleccion } from './SelectorParteTema'

// Origen de la parte de la segunda obra: a mano, autorrellenada o sin equivalente.
type OrigenParteOtra = 'manual' | 'auto' | 'sin-equivalente'

const normalizar = (texto: string) => texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim()

// Parte de la segunda obra en una comparativa. En «misma escena» se autorrellena
// por nombre con la parte elegida en la obra principal, salvo si el autor la fija a mano.
export function useParteOtra(comparativa: EstadoComparativa, parteLabel: string | null) {
  const [parteOtra, setParteOtra] = useState<Seleccion>(SIN_SELECCION)
  const [origen, setOrigen] = useState<OrigenParteOtra>('auto')
  const origenRef = useRef<OrigenParteOtra>('auto')

  const otraSlug = comparativa.obra?.slug ?? null
  const mismaEscena = comparativa.activa && comparativa.modo === 'misma_escena'

  // Al cambiar la segunda obra se descarta la parte elegida en ella.
  useEffect(() => {
    setParteOtra(SIN_SELECCION)
    origenRef.current = 'auto'
    setOrigen('auto')
  }, [otraSlug])

  useEffect(() => {
    if (!mismaEscena || !otraSlug || !parteLabel || origenRef.current === 'manual') return
    let vigente = true
    const nombre = parteLabel
    buscarUnidades(otraSlug, nombre).then((items) => {
      if (!vigente || origenRef.current === 'manual') return
      const igual = items.find((i) => normalizar(i.label) === normalizar(nombre))
      if (igual) {
        setParteOtra(igual)
        origenRef.current = 'auto'
        setOrigen('auto')
      } else {
        setParteOtra(SIN_SELECCION)
        origenRef.current = 'sin-equivalente'
        setOrigen('sin-equivalente')
      }
    })
    return () => {
      vigente = false
    }
  }, [mismaEscena, otraSlug, parteLabel])

  function elegir(seleccion: Seleccion) {
    setParteOtra(seleccion)
    // Vaciarla devuelve el control al autorrelleno.
    const nuevo: OrigenParteOtra = seleccion.id ? 'manual' : 'auto'
    origenRef.current = nuevo
    setOrigen(nuevo)
  }

  function pista(titulo: string) {
    if (!mismaEscena) return 'Solo lo verá quien haya llegado aquí y a la frontera de la obra principal.'
    if (origen === 'sin-equivalente' && parteLabel) {
      return `No hay una parte llamada «${parteLabel}» en ${titulo}: indícala.`
    }
    if (origen === 'auto' && parteOtra.id) {
      return 'Rellenada con la parte del mismo nombre. Cámbiala si no coincide.'
    }
    return `Así también lo verán quienes solo lleven ${titulo}.`
  }

  return { parteOtra, otraSlug, mismaEscena, elegir, pista }
}