import { useEffect, useState, type FormEvent } from 'react'
import styles from './EditProfileForm.module.css'
import { fetchProfileEditData, updateProfile, type ProfileEditData } from '../../api/profile'

export default function EditProfileForm() {
  const [datos, setDatos] = useState<ProfileEditData | null>(null)
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [bio, setBio] = useState('')
  const [interests, setInterests] = useState('')
  const [image, setImage] = useState<File | null>(null)
  const [errores, setErrores] = useState<string[]>([])
  const [guardado, setGuardado] = useState(false)
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    fetchProfileEditData().then((data) => {
      setDatos(data)
      setUsername(data.username)
      setEmail(data.email)
      setBio(data.bio)
      setInterests(data.interests)
    })
  }, [])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setErrores([])
    setGuardado(false)
    setCargando(true)
    try {
      const actualizado = await updateProfile({ username, email, bio, interests, image })
      setDatos((prev) => (prev ? { ...prev, ...actualizado } : prev))
      setGuardado(true)
    } catch (err) {
      if (err && typeof err === 'object') {
        const mensajes = Object.values(err as Record<string, unknown>).flat().map(String)
        setErrores(mensajes.length > 0 ? mensajes : ['No se pudo guardar. Inténtalo de nuevo.'])
      } else {
        setErrores(['No se pudo guardar. Inténtalo de nuevo.'])
      }
    } finally {
      setCargando(false)
    }
  }

  if (!datos) {
    return null
  }

  return (
    <div className={styles.wrapper}>
      <h1 className={styles.title}>Editar perfil</h1>

      <div className={styles.avatarPreview}>
        <img className={styles.avatarImg} src={datos.avatar_url} alt="" />
      </div>

      <form className={styles.form} onSubmit={handleSubmit}>
        {errores.map((msg, i) => (
          <p className={styles.error} key={i}>{msg}</p>
        ))}
        {guardado && <p className={styles.success}>Cambios guardados.</p>}

        <div className={styles.field}>
          <label className={styles.label} htmlFor="username">Usuario</label>
          <input
            id="username"
            className={styles.input}
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
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
          <label className={styles.label} htmlFor="bio">Bio</label>
          <textarea
            id="bio"
            className={styles.textarea}
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            placeholder="Cuéntanos algo sobre ti..."
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="interests">Intereses</label>
          <input
            id="interests"
            className={styles.input}
            type="text"
            value={interests}
            onChange={(e) => setInterests(e.target.value)}
            placeholder="Ej: deporte, programación, música..."
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="image">Avatar</label>
          <input
            id="image"
            className={styles.input}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => setImage(e.target.files?.[0] ?? null)}
          />
        </div>

        <button className={styles.submit} type="submit" disabled={cargando}>
          {cargando ? 'Guardando...' : 'Guardar cambios'}
        </button>
      </form>
    </div>
  )
}