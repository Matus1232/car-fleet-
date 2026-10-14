import { useCallback, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router'
import LoginForm from './components/LoginForm'
import VehiclesPage from './components/VehiclesPage'

const TOKEN_KEY = 'token'

function App() {
  // Pri štarte si token prečítame z localStorage, takže obnovenie stránky nikoho neodhlási.
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))

  function handleLogin(newToken: string) {
    localStorage.setItem(TOKEN_KEY, newToken)
    setToken(newToken)
  }

  // useCallback: funkcia ostane pri prekreslení tá istá, inak by ju useEffect
  // vo VehiclesPage považoval za zmenu a načítal autá znova.
  const handleLogout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
  }, [])

  return (
    <main>
      <header>
        <h1>Car Fleet Manager</h1>
        {token !== null && <button onClick={handleLogout}>Odhlásiť sa</button>}
      </header>

      <Routes>
        <Route
          path="/login"
          element={token === null ? <LoginForm onLogin={handleLogin} /> : <Navigate to="/vehicles" replace />}
        />
        <Route
          path="/vehicles"
          element={
            token === null ? (
              <Navigate to="/login" replace />
            ) : (
              <VehiclesPage token={token} onUnauthorized={handleLogout} />
            )
          }
        />
        {/* Akákoľvek iná adresa (aj "/") presmeruje na zoznam áut. */}
        <Route path="*" element={<Navigate to="/vehicles" replace />} />
      </Routes>
    </main>
  )
}

export default App
