import { useState, type FormEvent } from 'react'
import styles from './EditProfileForm.module.css'
import botones from '../../styles/botones.module.css'
import { cambiarPassword } from '../../api/auth'
import { ApiError } from '../../api/client'

const ERROR_GENERICO = 'No se pudo cambiar la contraseña. Inténtalo de nuevo.'

export default function CambioPasswordForm() {
  const [actual, setActual] = useState('')
  const [nueva, setNueva] = useState('')
  const [nueva2, setNueva2] = useState('')
  const [errores, setErrores] = useState<string[]>([])
  const [cambiada, setCambiada] = useState(false)
  const [cargando, setCargando] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setErrores([])
    setCambiada(false)
    setCargando(true)
    try {
      await cambiarPassword({ password_actual: actual, password: nueva, password2: nueva2 })
      setActual('')
      setNueva('')
      setNueva2('')
      setCambiada(true)
    } catch (err) {
      // 403: límite de intentos por minuto, como en el login.
      if (err instanceof ApiError && err.status === 403) {
        setErrores(['Demasiados intentos. Prueba de nuevo en un minuto.'])
      } else if (err instanceof ApiError && err.detail && typeof err.detail === 'object') {
        const mensajes = Object.values(err.detail as Record<string, unknown>).flat().map(String)
        setErrores(mensajes.length > 0 ? mensajes : [ERROR_GENERICO])
      } else {
        setErrores([ERROR_GENERICO])
      }
    } finally {
      setCargando(false)
    }
  }

  return (
    <section className={styles.seccion}>
      <h2 className={styles.subtitle}>Cambiar contraseña</h2>

      <form className={styles.form} onSubmit={handleSubmit}>
        {errores.map((msg, i) => (
          <p className={styles.error} key={i}>{msg}</p>
        ))}
        {cambiada && <p className={styles.success}>Contraseña cambiada.</p>}

        <div className={styles.field}>
          <label className={styles.label} htmlFor="password-actual">Contraseña actual</label>
          <input
            id="password-actual"
            className={styles.input}
            type="password"
            autoComplete="current-password"
            value={actual}
            onChange={(e) => setActual(e.target.value)}
            required
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="password-nueva">Contraseña nueva</label>
          <input
            id="password-nueva"
            className={styles.input}
            type="password"
            autoComplete="new-password"
            value={nueva}
            onChange={(e) => setNueva(e.target.value)}
            required
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="password-nueva2">Repite la contraseña nueva</label>
          <input
            id="password-nueva2"
            className={styles.input}
            type="password"
            autoComplete="new-password"
            value={nueva2}
            onChange={(e) => setNueva2(e.target.value)}
            required
          />
        </div>

        <button className={`${botones.primario} ${styles.submit}`} type="submit" disabled={cargando}>
          {cargando ? 'Cambiando...' : 'Cambiar contraseña'}
        </button>
      </form>
    </section>
  )
}