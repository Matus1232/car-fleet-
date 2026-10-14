import { useEffect, useState } from 'react'
import { getVehicles } from '../api'
import type { VehiclePage } from '../types'
import VehicleList from './VehicleList'

type Props = {
  token: string
}

function VehiclesPage({ token }: Props) {
  const [page, setPage] = useState<VehiclePage | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Spustí sa po prvom zobrazení komponentu a potom znova vždy, keď sa zmení token.
  useEffect(() => {
    // Ak komponent zmizne skôr, než príde odpoveď, výsledok už nechceme zapisovať do state.
    let ignore = false

    getVehicles(token)
      .then((data) => {
        if (!ignore) setPage(data)
      })
      .catch((err) => {
        if (ignore) return
        setError(err instanceof TypeError ? 'Server je nedostupný.' : err.message)
      })

    return () => {
      ignore = true
    }
  }, [token])

  if (error !== null) {
    return <p className="error">{error}</p>
  }
  if (page === null) {
    return <p>Načítavam…</p>
  }

  return (
    <>
      <p>Počet áut: {page.total}</p>
      <VehicleList vehicles={page.items} />
    </>
  )
}

export default VehiclesPage
