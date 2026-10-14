import { useEffect, useState } from 'react'
import { createVehicle, deleteVehicle, errorMessage, getVehicles, UnauthorizedError, updateVehicle } from '../api'
import type { Vehicle, VehicleInput, VehiclePage } from '../types'
import Pagination from './Pagination'
import VehicleForm from './VehicleForm'
import VehicleList from './VehicleList'

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
  const [skip, setSkip] = useState(0)
  // Počítadlo, ktoré len zvyšujeme. Je v závislostiach useEffect, takže jeho zmena = načítaj znova.
  const [reloadCount, setReloadCount] = useState(0)

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
      if (editing?.id === vehicle.id) closeForm() // zmazané auto už nemá zmysel upravovať
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

  function openCreate() {
    setEditing(null)
    setShowForm(true)
  }

  function openEdit(vehicle: Vehicle) {
    setEditing(vehicle)
    setShowForm(true)
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
    return <p>Načítavam…</p>
  }

  return (
    <>
      <div className="toolbar">
        <p>Počet áut: {page.total}</p>
        {isAdmin && !showForm && <button onClick={openCreate}>Pridať auto</button>}
      </div>
      {showForm && (
        // key: pri prepnutí na iné auto React vytvorí formulár nanovo, s hodnotami nového auta.
        <VehicleForm key={editing?.id ?? 'new'} initial={editing} onSave={handleSave} onCancel={closeForm} />
      )}
      {deleteError && <p className="error">{deleteError}</p>}
      <VehicleList
        vehicles={page.items}
        onEdit={isAdmin ? openEdit : undefined}
        onDelete={isAdmin ? handleDelete : undefined}
      />
      <Pagination skip={skip} limit={PAGE_SIZE} total={page.total} onChange={setSkip} />
    </>
  )
}

export default VehiclesPage
