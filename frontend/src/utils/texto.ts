// Comparación de nombres sin tildes, mayúsculas ni espacios sobrantes.
export const normalizar = (texto: string) =>
  texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim()