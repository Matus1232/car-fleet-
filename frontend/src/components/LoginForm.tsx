import { useState } from 'react'
import type { FormEvent } from 'react'
import { login } from '../api'

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
      // fetch hodí TypeError, keď sa na server vôbec nedá pripojiť (napr. nebeží Docker).
      if (err instanceof TypeError) {
        setError('Server je nedostupný.')
      } else if (err instanceof Error) {
        setError(err.message)
      }
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
