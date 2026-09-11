import { useEffect, useState } from 'react'

const BREAKPOINT = 768

export function useIsMobile(): boolean {
  const [isMobile, setIsMobile] = useState(
    typeof window !== 'undefined' ? window.innerWidth < BREAKPOINT : false
  )

  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${BREAKPOINT - 1}px)`)
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches)
    mql.addEventListener('change', handler)
    return () => mql.removeEventListener('change', handler)
  }, [])

  return isMobile
}