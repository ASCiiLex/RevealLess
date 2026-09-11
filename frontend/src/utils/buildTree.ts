import type { UnidadNarrativa } from '../api/progreso'

export interface TreeNode extends UnidadNarrativa {
  hijos: TreeNode[]
}

export function buildTree(unidades: UnidadNarrativa[]): TreeNode[] {
  const porId = new Map<number, TreeNode>()
  unidades.forEach((u) => porId.set(u.id, { ...u, hijos: [] }))

  const raices: TreeNode[] = []
  porId.forEach((nodo) => {
    if (nodo.padre === null) {
      raices.push(nodo)
    } else {
      const padre = porId.get(nodo.padre)
      if (padre) {
        padre.hijos.push(nodo)
      }
    }
  })

  const ordenar = (nodos: TreeNode[]) => {
    nodos.sort((a, b) => a.orden_inicio - b.orden_inicio)
    nodos.forEach((n) => ordenar(n.hijos))
  }
  ordenar(raices)

  return raices
}

/** true si esta unidad o alguno de sus descendientes es la unidad actual
 * (comparando por rango, ya que la unidad actual es siempre una hoja). */
export function contieneActual(nodo: TreeNode, actualId: number): boolean {
  if (nodo.id === actualId) return true
  return nodo.hijos.some((h) => contieneActual(h, actualId))
}