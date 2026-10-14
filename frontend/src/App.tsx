import { useCallback, useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router'
import { getMe, UnauthorizedError } from './api'
import LoginForm from './components/LoginForm'
import VehiclesPage from './components/VehiclesPage'
import type { User } from './types'

const TOKEN_KEY = 'token'

function App() {
  // Pri štarte si token prečítame z localStorage, takže obnovenie stránky nikoho neodhlási.
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState<User | null>(null)

  function handleLogin(newToken: string) {
    localStorage.setItem(TOKEN_KEY, newToken)
    setToken(newToken)
  }

  // useCallback: funkcia ostane pri prekreslení tá istá, inak by ju useEffect
  // vo VehiclesPage považoval za zmenu a načítal autá znova.
  const handleLogout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
  }, [])

  // Keď máme token, zistíme, komu patrí (email a rola).
  useEffect(() => {
    if (token === null) return
    let ignore = false

    getMe(token)
      .then((me) => {
        if (!ignore) setUser(me)
      })
      .catch((err) => {
        // Iné chyby (napr. nedostupný server) tu ignorujeme, ukáže ich VehiclesPage.
        if (!ignore && err instanceof UnauthorizedError) handleLogout()
      })

    return () => {
      ignore = true
    }
  }, [token, handleLogout])

  return (
    <main>
      <header>
        <h1>Car Fleet Manager</h1>
        {token !== null && (
          <div className="user">
            {user && (
              <span>
                {user.email} ({user.role})
              </span>
            )}
            <button onClick={handleLogout}>Odhlásiť sa</button>
          </div>
        )}
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
              <VehiclesPage token={token} isAdmin={user?.role === 'admin'} onUnauthorized={handleLogout} />
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
