import { Link } from 'react-router'
import type { User } from '../types'

type Props = {
  user: User | null // null, kým zo servera nepríde odpoveď na "kto som"
}

// Úvodná stránka po prihlásení: privítanie a menu s dvoma časťami aplikácie.
function HomePage({ user }: Props) {
  const isAdmin = user?.role === 'admin'

  return (
    <>
      <div className="welcome">
        <h2>Vitajte</h2>
        <p>
          {user && (
            <>
              Prihlásený účet <strong>{user.email}</strong>.{' '}
            </>
          )}
          Vyber si, kam chceš ísť.
        </p>
      </div>

      {/* <Link> vyzerá ako odkaz (<a>), ale stránku neobnoví: React Router len vymení obsah. */}
      <nav className="menu" aria-label="Hlavné menu">
        {/* Vozový park vidí len admin, bežný účet slúži len na rezerváciu servisu. */}
        {isAdmin && (
          <Link className="menu-card cars" to="/vehicles">
            <span className="menu-title">Vozový park</span>
            <span className="menu-text">Zoznam áut, platnosť STK a servisná história.</span>
            <span className="menu-go">Otvoriť →</span>
          </Link>
        )}

        <Link className="menu-card calendar-card" to="/bookings">
          <span className="menu-title">{isAdmin ? 'Rezervácie servisu' : 'Termín servisu'}</span>
          <span className="menu-text">
            {isAdmin
              ? 'Kalendár s termínmi, ktoré si ľudia rezervovali.'
              : 'Vyber si v kalendári deň a hodinu, kedy prídeš do servisu.'}
          </span>
          <span className="menu-go">Otvoriť →</span>
        </Link>
      </nav>
    </>
  )
}

export default HomePage
