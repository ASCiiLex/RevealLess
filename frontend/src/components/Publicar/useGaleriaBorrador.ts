import { useState } from 'react'
import { MAX_IMAGENES, ZOOM_BASE } from '../Galeria/GaleriaPost'
import type { CambioEncuadre, ImagenBorrador } from './GaleriaEditor'

// Imágenes aún sin publicar: previsualización local, etiqueta y encuadre por imagen.
export function useGaleriaBorrador() {
  const [imagenes, setImagenes] = useState<ImagenBorrador[]>([])
  const [disposicion, setDisposicion] = useState('')

  function anadir(archivos: File[]) {
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

  function quitar(indice: number) {
    URL.revokeObjectURL(imagenes[indice].url)
    setImagenes(imagenes.filter((_, i) => i !== indice))
  }

  function cambiarEtiqueta(indice: number, etiqueta: string) {
    setImagenes((prev) => prev.map((img, i) => (i === indice ? { ...img, etiqueta } : img)))
  }

  function cambiarEncuadre(indice: number, cambio: CambioEncuadre) {
    setImagenes((prev) => prev.map((img, i) => (i === indice ? { ...img, ...cambio } : img)))
  }

  return { imagenes, disposicion, setDisposicion, anadir, quitar, cambiarEtiqueta, cambiarEncuadre }
}