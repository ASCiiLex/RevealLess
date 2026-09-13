import { useState, type FormEvent } from 'react'
import styles from './AuthForm.module.css'
import AuthLayout from './AuthLayout'
import { register } from '../../api/auth'
import { ApiError } from '../../api/client'

export default function RegisterForm() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [password2, setPassword2] = useState('')
  const [image, setImage] = useState<File | null>(null)
  const [errores, setErrores] = useState<string[]>([])
  const [cargando, setCargando] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setErrores([])
    setCargando(true)
    try {
      await register({ username, email, password, password2, image })
      window.location.href = '/feed/react/'
    } catch (err) {
      if (err instanceof ApiError && err.detail && typeof err.detail === 'object') {
        const mensajes = Object.values(err.detail as Record<string, unknown>)
          .flat()
          .map((m) => String(m))
        setErrores(mensajes.length > 0 ? mensajes : ['No se pudo completar el registro.'])
      } else {
        setErrores(['No se pudo completar el registro. Inténtalo de nuevo.'])
      }
    } finally {
      setCargando(false)
    }
  }

  return (
    <AuthLayout
      titulo="Crear cuenta"
      footer={<span>¿Ya tienes cuenta? <a href="/cuentas/login-react/">Inicia sesión</a></span>}
    >
      <form className={styles.form} onSubmit={handleSubmit}>
        {errores.map((msg, i) => (
          <p className={styles.error} key={i}>{msg}</p>
        ))}

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
          <label className={styles.label} htmlFor="email">Email</label>
          <input
            id="email"
            className={styles.input}
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
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

        <div className={styles.field}>
          <label className={styles.label} htmlFor="password2">Repite la contraseña</label>
          <input
            id="password2"
            className={styles.input}
            type="password"
            value={password2}
            onChange={(e) => setPassword2(e.target.value)}
            required
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="image">Avatar (opcional)</label>
          <input
            id="image"
            className={styles.input}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => setImage(e.target.files?.[0] ?? null)}
          />
        </div>

        <button className={styles.submit} type="submit" disabled={cargando}>
          {cargando ? 'Creando cuenta...' : 'Crear cuenta'}
        </button>
      </form>
    </AuthLayout>
  )
}