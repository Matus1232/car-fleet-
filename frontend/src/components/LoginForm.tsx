import { useState } from 'react'
import type { FormEvent } from 'react'
import { errorMessage, login } from '../api'

type Props = {
  onLogin: (token: string) => void
}

function LoginForm({ onLogin }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault() // inak by prehliadač po odoslaní znova načítal celú stránku
    setError(null)
    setLoading(true)
    try {
      const token = await login(email, password)
      onLogin(token)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2>Prihlásenie</h2>

      <label>
        E-mail
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
          autoFocus // kurzor bude v tomto políčku hneď po načítaní stránky
        />
      </label>

      <label>
        Heslo
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
      </label>

      {error && <p className="error">{error}</p>}

      <button type="submit" disabled={loading}>
        {loading ? 'Prihlasujem…' : 'Prihlásiť sa'}
      </button>
    </form>
  )
}

export default LoginForm
