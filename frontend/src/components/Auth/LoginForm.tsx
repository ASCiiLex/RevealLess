import { useState, type FormEvent } from 'react'
import styles from './AuthForm.module.css'
import AuthLayout from './AuthLayout'
import { login } from '../../api/auth'
import { ApiError } from '../../api/client'

export default function LoginForm() {
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
      window.location.href = '/feed/react/'
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
    <AuthLayout
      titulo="Iniciar sesión"
      footer={<span>¿No tienes cuenta? <a href="/cuentas/register-react/">Regístrate</a></span>}
    >
      <form className={styles.form} onSubmit={handleSubmit}>
        {error && <p className={styles.error}>{error}</p>}

        <div className={styles.field}>
          <label className={styles.label} htmlFor="username">Usuario</label>
          <input
            id="username"
            className={styles.input}
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoFocus
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="password">Contraseña</label>
          <input
            id="password"
            className={styles.input}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button className={styles.submit} type="submit" disabled={cargando}>
          {cargando ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </AuthLayout>
  )
}