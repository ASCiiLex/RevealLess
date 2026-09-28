import { useState, type FormEvent } from 'react'
import formStyles from './AuthForm.module.css'
import styles from './HeroLoginForm.module.css'
import { login } from '../../api/auth'
import { ApiError } from '../../api/client'

// Versión compacta de LoginForm para el hero de la landing pública.
export default function HeroLoginForm() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [cargando, setCargando] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setCargando(true)
    try {
      await login(username, password)
      window.location.href = '/feed/'
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setError('Usuario o contraseña incorrectos')
      } else if (err instanceof ApiError && err.status === 403) {
        setError('Demasiados intentos. Prueba de nuevo en un minuto.')
      } else {
        setError('No se pudo iniciar sesión. Inténtalo de nuevo.')
      }
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className={styles.card}>
      <h2 className={styles.title}>Iniciar sesión</h2>

      <form className={formStyles.form} onSubmit={handleSubmit}>
        {error && <p className={formStyles.error}>{error}</p>}

        <div className={formStyles.field}>
          <label className={formStyles.label} htmlFor="hero-username">Usuario</label>
          <input
            id="hero-username"
            className={formStyles.input}
            type="text"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>

        <div className={formStyles.field}>
          <label className={formStyles.label} htmlFor="hero-password">Contraseña</label>
          <input
            id="hero-password"
            className={formStyles.input}
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button className={formStyles.submit} type="submit" disabled={cargando}>
          {cargando ? 'Entrando...' : 'Entrar'}
        </button>
      </form>

      <p className={styles.footer}>
        ¿No tienes cuenta? <a href="/cuentas/register/">Regístrate</a>
      </p>
    </div>
  )
}