import { useState, type FormEvent } from 'react'
import styles from './AuthForm.module.css'
import AuthLayout from './AuthLayout'
import OnboardingSearch from './OnboardingSearch'
import { register } from '../../api/auth'
import { ApiError } from '../../api/client'

type Paso = 'form' | 'onboarding'

export default function RegisterForm() {
  const [paso, setPaso] = useState<Paso>('form')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [password2, setPassword2] = useState('')
  const [image, setImage] = useState<File | null>(null)
  const [errores, setErrores] = useState<string[]>([])
  const [cargando, setCargando] = useState(false)
  const [totalSeguidos, setTotalSeguidos] = useState(0)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setErrores([])
    setCargando(true)
    try {
      await register({ username, email, password, password2, image })
      setPaso('onboarding')
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

  function finalizarOnboarding() {
    // Si no siguio nada, Biblioteca estaria vacia -- lo llevamos
    // directamente a Descubrir para que aterrice con contenido.
    window.location.href = totalSeguidos > 0 ? '/feed/' : '/feed/?view=descubrir'
  }

  if (paso === 'onboarding') {
    return (
      <AuthLayout titulo="¿Qué te interesa?">
        <p style={{ fontSize: 13, color: 'var(--fog)', marginBottom: 12 }}>
          Sigue alguna obra o tema para empezar con contenido en tu Biblioteca. Puedes hacerlo también más tarde.
        </p>
        <OnboardingSearch onCambioContador={setTotalSeguidos} />
        <button
          className={styles.submit}
          style={{ marginTop: 16 }}
          onClick={finalizarOnboarding}
        >
          {totalSeguidos > 0 ? 'Continuar a Biblioteca' : 'Continuar a Descubrir'}
        </button>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout
      titulo="Crear cuenta"
      footer={<span>¿Ya tienes cuenta? <a href="/cuentas/login/">Inicia sesión</a></span>}
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