import { useCallback, useEffect, useState } from 'react'
import { Link, Navigate, NavLink, Route, Routes } from 'react-router'
import { getMe, UnauthorizedError } from './api'
import BookingsPage from './components/BookingsPage'
import HomePage from './components/HomePage'
import LoginForm from './components/LoginForm'
import RegisterForm from './components/RegisterForm'
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
        // Iné chyby (napr. nedostupný server) tu ignorujeme, ukáže ich otvorená stránka.
        if (!ignore && err instanceof UnauthorizedError) handleLogout()
      })

    return () => {
      ignore = true
    }
  }, [token, handleLogout])

  const isAdmin = user?.role === 'admin'

  return (
    <>
      {/* header je mimo <main>, aby biely pás mohol ísť cez celú šírku okna */}
      <header>
        <div className="header-inner">
          <div className="brand">
            <h1>
              <Link to="/">Car Fleet Manager</Link>
            </h1>
            {token !== null && (
              // NavLink je Link, ktorý vie, či ukazuje na práve otvorenú stránku: vtedy dostane
              // triedu "active" a aria-current="page". CSS podľa toho kreslí čiaru pod odkazom.
              <nav className="nav" aria-label="Stránky">
                {isAdmin && <NavLink to="/vehicles">Vozidlá</NavLink>}
                <NavLink to="/bookings">Servis</NavLink>
              </nav>
            )}
          </div>
          {token !== null && (
            <div className="user">
              {user && (
                <>
                  <span>{user.email}</span>
                  <span className="role">{user.role}</span>
                </>
              )}
              <button className="secondary" onClick={handleLogout}>
                Odhlásiť sa
              </button>
            </div>
          )}
        </div>
      </header>

      <main>
        {/* Dve sady stránok podľa toho, či je niekto prihlásený. V každej sade posledná cesta
            "*" zachytí všetko ostatné, takže neprihlásený sa z /vehicles dostane na prihlásenie
            a prihlásený z /login na úvodnú stránku. */}
        {token === null ? (
          <Routes>
            <Route path="/login" element={<LoginForm onLogin={handleLogin} />} />
            <Route path="/register" element={<RegisterForm onLogin={handleLogin} />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        ) : (
          <Routes>
            <Route path="/" element={<HomePage user={user} />} />
            <Route
              path="/vehicles"
              element={
                // Vozový park je len pre admina. Kým nevieme, kto je prihlásený (user je null),
                // ukážeme načítavanie, inak by sme admina po obnovení stránky omylom presmerovali.
                // Je to len pohodlie: backend by bežnému účtu aj tak vrátil 403.
                user === null ? (
                  <p className="loading">Načítavam…</p>
                ) : isAdmin ? (
                  <VehiclesPage token={token} isAdmin={isAdmin} onUnauthorized={handleLogout} />
                ) : (
                  <Navigate to="/" replace />
                )
              }
            />
            <Route
              path="/bookings"
              element={<BookingsPage token={token} isAdmin={isAdmin} onUnauthorized={handleLogout} />}
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        )}
      </main>
    </>
  )
}

export default App
