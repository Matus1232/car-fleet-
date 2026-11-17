import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router'
import { errorMessage, login, register } from '../api'

type Props = {
  onLogin: () => Promise<void> // volá sa po registrácii a prihlásení (pozri LoginForm)
}

function RegisterForm({ onLogin }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordAgain, setPasswordAgain] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    // Heslo sa pri písaní nezobrazuje, takže preklep si človek nevšimne. Preto ho píše dvakrát
    // a porovnáme to tu; na server sa posiela len jedno.
    if (password !== passwordAgain) {
      setError('Heslá sa nezhodujú.')
      return
    }

    setError(null)
    setLoading(true)
    try {
      await register(email, password)
      // Registrácia neprihlasuje, tak používateľa rovno prihlásime tými istými údajmi.
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
      <h2>Nový účet</h2>
      <p className="hint">Po registrácii si môžeš rezervovať termín servisu.</p>

      <label>
        E-mail
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="email"
          required
        />
      </label>

      {/* minLength a maxLength sú rovnaké hranice ako na backende (UserRegister). */}
      <label>
        Heslo (aspoň 8 znakov)
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="new-password"
          minLength={8}
          maxLength={128}
          required
        />
      </label>

      <label>
        Heslo znova
        <input
          type="password"
          value={passwordAgain}
          onChange={(event) => setPasswordAgain(event.target.value)}
          autoComplete="new-password"
          required
        />
      </label>

      {error && <p className="error">{error}</p>}

      <button type="submit" disabled={loading}>
        {loading ? 'Vytváram účet…' : 'Zaregistrovať sa'}
      </button>

      <p className="form-footer">
        Už máš účet? <Link to="/login">Prihlás sa</Link>
      </p>
    </form>
  )
}

export default RegisterForm
