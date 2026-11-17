import { useEffect, useState } from 'react'
import { getVehicleStats, UnauthorizedError } from '../api'
import { STK_SOON_DAYS } from '../dates'
import type { StkFilter, VehicleStats } from '../types'

type Props = {
  // Číslo, ktoré rodič zvýši po každej zmene áut. Je v závislostiach useEffect, takže jeho
  // zmena = načítaj štatistiky znova (rovnaký trik ako reloadCount vo VehiclesPage).
  version: number
  // Ktorý filter je práve zapnutý (null = všetky autá). Pamätá si ho rodič, lebo podľa neho
  // načítava tabuľku; dashboard ho len ukáže a kliknutie oznámi cez onFilter.
  filter: StkFilter | null
  onFilter: (filter: StkFilter | null) => void
  onUnauthorized: () => void
}

function Dashboard({ version, filter, onFilter, onUnauthorized }: Props) {
  const [stats, setStats] = useState<VehicleStats | null>(null)

  useEffect(() => {
    let ignore = false

    getVehicleStats()
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
  }, [version, onUnauthorized])

  // Kým dáta neprišli, namiesto čísla ukážeme pomlčku. stats?.total je undefined, keď stats je null.
  const show = (value: number | undefined) => value ?? '–'

  // Všetky tri čísla sa líšia len hodnotou, textom a filtrom, tak ich opíšeme zoznamom
  // a tlačidlá vyrobíme cez map() nižšie, namiesto troch skoro rovnakých kusov JSX.
  const items: { filter: StkFilter | null; value: number | undefined; label: string; alert?: boolean }[] = [
    { filter: null, value: stats?.total, label: 'Autá spolu' },
    { filter: 'expiring', value: stats?.stk_expiring, label: `STK končí do ${STK_SOON_DAYS} dní` },
    // Červená len vtedy, keď naozaj nejaké auto je po STK.
    { filter: 'expired', value: stats?.stk_expired, label: 'Po STK', alert: (stats?.stk_expired ?? 0) > 0 },
  ]

  return (
    // Obrys auta je obrázok na pozadí (.dashboard v index.css), preto tu preň nie je žiadny element.
    <section className="dashboard" aria-label="Prehľad vozového parku">
      {items.map((item) => (
        // <button> namiesto <div>: dá sa naň kliknúť aj prejsť klávesom Tab a stlačiť Enter.
        // aria-pressed povie čítačke obrazovky, ktorý filter je zapnutý; CSS podľa neho kreslí čiaru.
        <button
          key={item.label}
          type="button"
          className={item.alert ? 'stat alert' : 'stat'}
          aria-pressed={filter === item.filter}
          onClick={() => onFilter(item.filter)}
        >
          <span className="stat-value">{show(item.value)}</span>
          <span className="stat-label">{item.label}</span>
        </button>
      ))}
    </section>
  )
}

export default Dashboard
