import { useEffect, useState } from 'react'
import { getVehicleStats, UnauthorizedError } from '../api'
import { STK_SOON_DAYS } from '../dates'
import type { VehicleStats } from '../types'

type Props = {
  token: string
  // Číslo, ktoré rodič zvýši po každej zmene áut. Je v závislostiach useEffect, takže jeho
  // zmena = načítaj štatistiky znova (rovnaký trik ako reloadCount vo VehiclesPage).
  version: number
  onUnauthorized: () => void
}

function Dashboard({ token, version, onUnauthorized }: Props) {
  const [stats, setStats] = useState<VehicleStats | null>(null)

  useEffect(() => {
    let ignore = false

    getVehicleStats(token)
      .then((data) => {
        if (!ignore) setStats(data)
      })
      .catch((err) => {
        // Iné chyby tu neriešime: dashboard ostane s pomlčkami a chybu ukáže zoznam áut pod ním.
        if (!ignore && err instanceof UnauthorizedError) onUnauthorized()
      })

    return () => {
      ignore = true
    }
  }, [token, version, onUnauthorized])

  // Kým dáta neprišli, namiesto čísla ukážeme pomlčku. stats?.total je undefined, keď stats je null.
  const show = (value: number | undefined) => value ?? '–'

  return (
    // Obrys auta je obrázok na pozadí (.dashboard v index.css), preto tu preň nie je žiadny element.
    <section className="dashboard" aria-label="Prehľad vozového parku">
      <div className="stat">
        <span className="stat-value">{show(stats?.total)}</span>
        <span className="stat-label">Autá spolu</span>
      </div>
      <div className="stat">
        <span className="stat-value">{show(stats?.stk_expiring)}</span>
        <span className="stat-label">STK končí do {STK_SOON_DAYS} dní</span>
      </div>
      {/* Červená len vtedy, keď naozaj nejaké auto je po STK. */}
      <div className={stats && stats.stk_expired > 0 ? 'stat alert' : 'stat'}>
        <span className="stat-value">{show(stats?.stk_expired)}</span>
        <span className="stat-label">Po STK</span>
      </div>
    </section>
  )
}

export default Dashboard
