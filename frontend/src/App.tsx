import { useState } from 'react'
import LoginForm from './components/LoginForm'
import VehiclesPage from './components/VehiclesPage'

function App() {
  // null = nikto nie je prihlásený. Token je zatiaľ len v pamäti, po obnovení stránky zmizne.
  const [token, setToken] = useState<string | null>(null)

  return (
    <main>
      <h1>Car Fleet Manager</h1>
      {token === null ? <LoginForm onLogin={setToken} /> : <VehiclesPage token={token} />}
    </main>
  )
}

export default App
