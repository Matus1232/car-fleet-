import { useEffect, useState } from 'react'
import { createVehicle, deleteVehicle, errorMessage, getVehicles, UnauthorizedError, updateVehicle } from '../api'
import type { Vehicle, VehicleInput, VehiclePage } from '../types'
import Dashboard from './Dashboard'
import Pagination from './Pagination'
import VehicleForm from './VehicleForm'
import VehicleList from './VehicleList'
import VehicleServices from './VehicleServices'

const PAGE_SIZE = 10

type Props = {
  token: string
  isAdmin: boolean
  onUnauthorized: () => void
}

function VehiclesPage({ token, isAdmin, onUnauthorized }: Props) {
  const [page, setPage] = useState<VehiclePage | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Vehicle | null>(null) // null = formulár pridáva nové auto
  const [servicing, setServicing] = useState<Vehicle | null>(null) // auto, ktorého servis je otvorený
  const [skip, setSkip] = useState(0)
  // Počítadlo, ktoré len zvyšujeme. Je v závislostiach useEffect, takže jeho zmena = načítaj znova.
  const [reloadCount, setReloadCount] = useState(0)
  // To isté pre dashboard: zvýšime ho po každom pridaní, úprave a zmazaní auta.
  const [statsVersion, setStatsVersion] = useState(0)

  // Spustí sa po prvom zobrazení a potom vždy, keď sa zmení token, strana alebo reloadCount.
  useEffect(() => {
    // Ak komponent zmizne skôr, než príde odpoveď, výsledok už nechceme zapisovať do state.
    let ignore = false

    getVehicles(token, skip, PAGE_SIZE)
      .then((data) => {
        if (!ignore) setPage(data)
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
  }, [token, skip, reloadCount, onUnauthorized])

  function reload() {
    setReloadCount((count) => count + 1)
  }

  function retry() {
    setError(null)
    reload()
  }

  async function handleDelete(vehicle: Vehicle) {
    if (!confirm(`Naozaj zmazať auto ${vehicle.license_plate}?`)) return

    setDeleteError(null)
    try {
      await deleteVehicle(token, vehicle.id)
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
        await createVehicle(token, data)
        // Nové auto má najväčšie id, takže je na poslednej strane. Prejdeme tam.
        const total = (page?.total ?? 0) + 1
        setSkip(Math.floor((total - 1) / PAGE_SIZE) * PAGE_SIZE)
        reload()
      } else {
        const updated = await updateVehicle(token, editing.id, data)
        // Upravené auto vymeníme na jeho mieste, ostatné necháme tak.
        setPage((prev) => prev && { ...prev, items: prev.items.map((v) => (v.id === updated.id ? updated : v)) })
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
      <Dashboard token={token} version={statsVersion} onUnauthorized={onUnauthorized} />
      <div className="toolbar">
        <h2>
          Vozidlá<span className="count">{page.total}</span>
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
          token={token}
          vehicle={servicing}
          isAdmin={isAdmin}
          onClose={() => setServicing(null)}
          onUnauthorized={onUnauthorized}
        />
      )}
      {deleteError && <p className="error">{deleteError}</p>}
      <VehicleList
        vehicles={page.items}
        onServices={openServices}
        onEdit={isAdmin ? openEdit : undefined}
        onDelete={isAdmin ? handleDelete : undefined}
      />
      <Pagination skip={skip} limit={PAGE_SIZE} total={page.total} onChange={setSkip} />
    </>
  )
}

export default VehiclesPage
