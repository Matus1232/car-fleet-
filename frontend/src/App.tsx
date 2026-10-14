import { useState } from 'react'
import LoginForm from './components/LoginForm'
import VehicleList from './components/VehicleList'
import type { Vehicle } from './types'

// Dočasné ručne napísané dáta. V kroku 5 ich nahradíme dátami z backendu.
const sampleVehicles: Vehicle[] = [
  { id: 1, brand: 'Škoda', model: 'Octavia', license_plate: 'BA123AB', created_at: '2026-09-01T08:00:00Z' },
  { id: 2, brand: 'Volkswagen', model: 'Passat', license_plate: 'KE456CD', created_at: '2026-09-15T12:30:00Z' },
  { id: 3, brand: 'Toyota', model: 'Corolla', license_plate: 'ZA789EF', created_at: '2026-10-02T09:15:00Z' },
]

function App() {
  // null = nikto nie je prihlásený. Token je zatiaľ len v pamäti, po obnovení stránky zmizne.
  const [token, setToken] = useState<string | null>(null)

  return (
    <main>
      <h1>Car Fleet Manager</h1>
      {token === null ? (
        <LoginForm onLogin={setToken} />
      ) : (
        <VehicleList vehicles={sampleVehicles} />
      )}
    </main>
  )
}

export default App
