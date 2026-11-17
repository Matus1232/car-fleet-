import { useEffect, useState } from 'react'
import {
  createVehicle,
  deleteVehicle,
  errorMessage,
  getVehicles,
  getVehicleStats,
  UnauthorizedError,
  updateVehicle,
} from '../api'
import { STK_SOON_DAYS } from '../dates'
import type { StkFilter, Vehicle, VehicleInput, VehiclePage } from '../types'
import Dashboard from './Dashboard'
import Pagination from './Pagination'
import VehicleForm from './VehicleForm'
import VehicleList from './VehicleList'
import VehicleServices from './VehicleServices'

const PAGE_SIZE = 10

// Kde začína posledná strana: pri 23 autách a 10 na stranu je to skip 20 (autá 21 až 23).
function lastPageSkip(total: number): number {
  return Math.floor((total - 1) / PAGE_SIZE) * PAGE_SIZE
}

// Texty pre zapnutý filter: nadpis nad tabuľkou a správa, keď filtru nič nevyhovuje.
const FILTER_TEXTS: Record<StkFilter, { title: string; empty: string }> = {
  expiring: {
    title: `STK končí do ${STK_SOON_DAYS} dní`,
    empty: `Žiadnemu autu nekončí STK do ${STK_SOON_DAYS} dní.`,
  },
  expired: { title: 'Po STK', empty: 'Žiadne auto nie je po STK.' },
}

type Props = {
  isAdmin: boolean
  onUnauthorized: () => void
}

function VehiclesPage({ isAdmin, onUnauthorized }: Props) {
  const [page, setPage] = useState<VehiclePage | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Vehicle | null>(null) // null = formulár pridáva nové auto
  const [servicing, setServicing] = useState<Vehicle | null>(null) // auto, ktorého servis je otvorený
  const [skip, setSkip] = useState(0)
  // Filter z dashboardu: null = všetky autá, inak len tie s končiacou alebo neplatnou STK.
  const [stkFilter, setStkFilter] = useState<StkFilter | null>(null)
  // Počítadlo, ktoré len zvyšujeme. Je v závislostiach useEffect, takže jeho zmena = načítaj znova.
  const [reloadCount, setReloadCount] = useState(0)
  // To isté pre dashboard: zvýšime ho po každom pridaní, úprave a zmazaní auta.
  const [statsVersion, setStatsVersion] = useState(0)

  // Spustí sa po prvom zobrazení a potom vždy, keď sa zmení strana, filter alebo reloadCount.
  useEffect(() => {
    // Ak komponent zmizne skôr, než príde odpoveď, výsledok už nechceme zapisovať do state.
    let ignore = false

    getVehicles(skip, PAGE_SIZE, stkFilter)
      .then((data) => {
        if (ignore) return
        if (data.items.length === 0 && data.total > 0) {
          // Strana je prázdna, hoci autá existujú (napr. po úprave auto vypadlo z filtra
          // a bolo na strane posledné). Skočíme na poslednú stranu, ktorá ešte existuje.
          setSkip(lastPageSkip(data.total))
        } else {
          setPage(data)
        }
      })
      .catch((err) => {
        if (ignore) return
        if (err instanceof UnauthorizedError) {
          onUnauthorized() // token vypršal alebo je neplatný -> späť na prihlásenie
        } else {
          setError(errorMessage(err))
        }
      })

    return () => {
      ignore = true
    }
  }, [skip, stkFilter, reloadCount, onUnauthorized])

  function reload() {
    setReloadCount((count) => count + 1)
  }

  // Klik na číslo v dashboarde. Vyfiltrovaný zoznam má iný počet strán, preto začneme od prvej.
  function changeFilter(filter: StkFilter | null) {
    setStkFilter(filter)
    setSkip(0)
  }

  function retry() {
    setError(null)
    reload()
  }

  async function handleDelete(vehicle: Vehicle) {
    if (!confirm(`Naozaj zmazať auto ${vehicle.license_plate}?`)) return

    setDeleteError(null)
    try {
      await deleteVehicle(vehicle.id)
      setStatsVersion((version) => version + 1)
      if (editing?.id === vehicle.id) closeForm() // zmazané auto už nemá zmysel upravovať
      if (servicing?.id === vehicle.id) setServicing(null) // jeho servis zmizol spolu s ním
      // Bolo to posledné auto na strane? Vráť sa o stranu späť, inak načítaj tú istú znova.
      if (page !== null && page.items.length === 1 && skip > 0) {
        setSkip(skip - PAGE_SIZE)
      } else {
        reload()
      }
    } catch (err) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized()
      } else {
        setDeleteError(errorMessage(err))
      }
    }
  }

  // Nad tabuľkou je naraz otvorené len jedno: buď formulár auta, alebo jeho servis.
  function openCreate() {
    setServicing(null)
    setEditing(null)
    setShowForm(true)
  }

  function openEdit(vehicle: Vehicle) {
    setServicing(null)
    setEditing(vehicle)
    setShowForm(true)
  }

  function openServices(vehicle: Vehicle) {
    closeForm()
    setServicing(vehicle)
  }

  function closeForm() {
    setShowForm(false)
    setEditing(null)
  }

  // Chybu z formulára necháme "prebublať" ďalej (throw), aby ju VehicleForm mohol zobraziť.
  async function handleSave(data: VehicleInput) {
    try {
      if (editing === null) {
        await createVehicle(data)
        // Nové auto má najväčšie id, takže je na poslednej strane všetkých áut. Prejdeme tam.
        // Pri zapnutom filtri page.total ráta len vyfiltrované autá, preto si počet všetkých
        // vypýtame zo štatistík (tie už nové auto započítali) a filter vypneme.
        const total = stkFilter === null ? (page?.total ?? 0) + 1 : (await getVehicleStats()).total
        setStkFilter(null)
        setSkip(lastPageSkip(total))
        reload()
      } else {
        const updated = await updateVehicle(editing.id, data)
        if (stkFilter === null) {
          // Upravené auto vymeníme na jeho mieste, ostatné necháme tak.
          setPage((prev) => prev && { ...prev, items: prev.items.map((v) => (v.id === updated.id ? updated : v)) })
        } else {
          // Pri filtri mohla zmena dátumu STK auto zo zoznamu vyradiť, tak ho načítame znova.
          reload()
        }
      }
      setStatsVersion((version) => version + 1)
      closeForm()
    } catch (err) {
      if (err instanceof UnauthorizedError) onUnauthorized()
      throw err
    }
  }

  if (error !== null) {
    return (
      <div className="error">
        <p>{error}</p>
        <button onClick={retry}>Skúsiť znova</button>
      </div>
    )
  }
  if (page === null) {
    return <p className="loading">Načítavam…</p>
  }

  return (
    <>
      <Dashboard
        version={statsVersion}
        filter={stkFilter}
        onFilter={changeFilter}
        onUnauthorized={onUnauthorized}
      />
      <div className="toolbar">
        <h2>
          {stkFilter === null ? 'Vozidlá' : FILTER_TEXTS[stkFilter].title}
          <span className="count">{page.total}</span>
        </h2>
        {isAdmin && !showForm && <button onClick={openCreate}>Pridať auto</button>}
      </div>
      {showForm && (
        // key: pri prepnutí na iné auto React vytvorí formulár nanovo, s hodnotami nového auta.
        <VehicleForm key={editing?.id ?? 'new'} initial={editing} onSave={handleSave} onCancel={closeForm} />
      )}
      {servicing && (
        // key: pri prepnutí na iné auto sa panel vytvorí nanovo a načíta jeho záznamy.
        <VehicleServices
          key={servicing.id}
          vehicle={servicing}
          isAdmin={isAdmin}
          onClose={() => setServicing(null)}
          onUnauthorized={onUnauthorized}
        />
      )}
      {deleteError && <p className="error">{deleteError}</p>}
      <VehicleList
        vehicles={page.items}
        emptyText={stkFilter === null ? 'Zatiaľ tu nie sú žiadne autá.' : FILTER_TEXTS[stkFilter].empty}
        onServices={openServices}
        onEdit={isAdmin ? openEdit : undefined}
        onDelete={isAdmin ? handleDelete : undefined}
      />
      <Pagination skip={skip} limit={PAGE_SIZE} total={page.total} onChange={setSkip} />
    </>
  )
}

export default VehiclesPage
