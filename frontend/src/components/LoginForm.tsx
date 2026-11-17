import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router'
import { errorMessage, login } from '../api'

type Props = {
  // Volá sa po úspešnom prihlásení. Token sem neposielame: je v httpOnly cookie,
  // ktorú si prehliadač uložil sám a JavaScript ju nevidí.
  onLogin: () => Promise<void>
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
      await login(email, password)
      await onLogin()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="card login" onSubmit={handleSubmit}>
      <h2>Prihlásenie</h2>
      <p className="hint">Prihlás sa a uvidíš vozový park aj termíny servisu.</p>

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

      <p className="form-footer">
        Nemáš účet? <Link to="/register">Zaregistruj sa</Link>
      </p>
    </form>
  )
}

export default LoginForm
