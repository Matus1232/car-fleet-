import { useCallback, useEffect, useState } from 'react'
import { Link, Navigate, NavLink, Route, Routes } from 'react-router'
import { getMe, logout } from './api'
import BookingsPage from './components/BookingsPage'
import HomePage from './components/HomePage'
import LoginForm from './components/LoginForm'
import PriceListPage from './components/PriceListPage'
import RegisterForm from './components/RegisterForm'
import ShopPage from './components/ShopPage'
import VehiclesPage from './components/VehiclesPage'
import type { User } from './types'

function App() {
  // Token je v httpOnly cookie, ktorú JavaScript neprečíta. Či je niekto prihlásený, preto
  // zistíme len tak, že sa opýtame servera (GET /auth/me).
  // undefined = ešte sa pýtame, null = nikto nie je prihlásený, User = prihlásený.
  const [user, setUser] = useState<User | null | undefined>(undefined)

  useEffect(() => {
    // Staršia verzia aplikácie mala token v localStorage. Ak tam ešte je, zmažeme ho,
    // aby v prehliadači nezostal ležať. try: localStorage môže byť zakázaný (súkromné okno).
    try {
      localStorage.removeItem('token')
    } catch {
      // nič, nie je čo zmazať
    }

    let ignore = false
    getMe()
      .then((me) => {
        if (!ignore) setUser(me)
      })
      .catch(() => {
        // 401 = nikto nie je prihlásený. Pri inej chybe (napr. nedostupný server) to nevieme,
        // tak ukážeme prihlásenie; ak server nebeží, prihlasovací formulár to oznámi.
        if (!ignore) setUser(null)
      })

    return () => {
      ignore = true
    }
  }, [])

  // Po úspešnom prihlásení už má prehliadač cookie, stačí zistiť, komu patrí.
  async function handleLogin() {
    setUser(await getMe())
  }

  // Server odpovedal 401 (token vypršal alebo bol zrušený): len zabudneme používateľa.
  // useCallback: funkcia ostane pri prekreslení tá istá, inak by ju useEffect
  // na stránkach považoval za zmenu a načítal dáta znova.
  const handleUnauthorized = useCallback(() => setUser(null), [])

  // Tlačidlo Odhlásiť sa: backend token zruší a zmaže cookie. Aj keby to zlyhalo
  // (napr. nedostupný server), v aplikácii používateľa odhlásime.
  async function handleLogout() {
    try {
      await logout()
    } finally {
      setUser(null)
    }
  }

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
            {user && (
              // NavLink je Link, ktorý vie, či ukazuje na práve otvorenú stránku: vtedy dostane
              // triedu "active" a aria-current="page". CSS podľa toho kreslí čiaru pod odkazom.
              <nav className="nav" aria-label="Stránky">
                {isAdmin && <NavLink to="/vehicles">Vozidlá</NavLink>}
                <NavLink to="/bookings">Servis</NavLink>
                <NavLink to="/prices">Cenník</NavLink>
                <NavLink to="/shop">E-shop</NavLink>
              </nav>
            )}
          </div>
          {user && (
            <div className="user">
              <span>{user.email}</span>
              <span className="role">{user.role}</span>
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
            a prihlásený z /login na úvodnú stránku. Kým sa server neozve, nevieme ani jedno. */}
        {user === undefined ? (
          <p className="loading">Načítavam…</p>
        ) : user === null ? (
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
                // Vozový park je len pre admina. Je to len pohodlie: backend by bežnému účtu
                // aj tak vrátil 403.
                isAdmin ? (
                  <VehiclesPage isAdmin={isAdmin} onUnauthorized={handleUnauthorized} />
                ) : (
                  <Navigate to="/" replace />
                )
              }
            />
            <Route
              path="/bookings"
              element={<BookingsPage isAdmin={isAdmin} onUnauthorized={handleUnauthorized} />}
            />
            <Route path="/prices" element={<PriceListPage />} />
            <Route path="/shop" element={<ShopPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        )}
      </main>
    </>
  )
}

export default App
