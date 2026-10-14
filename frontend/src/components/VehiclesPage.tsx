import { useEffect, useState } from 'react'
import { createVehicle, deleteVehicle, errorMessage, getVehicles, UnauthorizedError } from '../api'
import type { Vehicle, VehicleInput, VehiclePage } from '../types'
import VehicleForm from './VehicleForm'
import VehicleList from './VehicleList'

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
        if (err instanceof UnauthorizedError) {
          onUnauthorized() // token vypršal alebo je neplatný -> späť na prihlásenie
        } else {
          setError(errorMessage(err))
        }
      })

    return () => {
      ignore = true
    }
  }, [token, onUnauthorized])

  async function handleDelete(vehicle: Vehicle) {
    if (!confirm(`Naozaj zmazať auto ${vehicle.license_plate}?`)) return

    setDeleteError(null)
    try {
      await deleteVehicle(token, vehicle.id)
      // Auto vyhodíme z už načítaného zoznamu, netreba znova sťahovať všetky autá.
      setPage((prev) =>
        prev && { ...prev, items: prev.items.filter((v) => v.id !== vehicle.id), total: prev.total - 1 },
      )
    } catch (err) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized()
      } else {
        setDeleteError(errorMessage(err))
      }
    }
  }

  // Chybu z formulára necháme "prebublať" ďalej (throw), aby ju VehicleForm mohol zobraziť.
  async function handleCreate(data: VehicleInput) {
    try {
      const created = await createVehicle(token, data)
      setPage((prev) => prev && { ...prev, items: [...prev.items, created], total: prev.total + 1 })
      setShowForm(false)
    } catch (err) {
      if (err instanceof UnauthorizedError) onUnauthorized()
      throw err
    }
  }

  if (error !== null) {
    return <p className="error">{error}</p>
  }
  if (page === null) {
    return <p>Načítavam…</p>
  }

  return (
    <>
      <div className="toolbar">
        <p>Počet áut: {page.total}</p>
        {isAdmin && !showForm && <button onClick={() => setShowForm(true)}>Pridať auto</button>}
      </div>
      {showForm && <VehicleForm onSave={handleCreate} onCancel={() => setShowForm(false)} />}
      {deleteError && <p className="error">{deleteError}</p>}
      <VehicleList vehicles={page.items} onDelete={isAdmin ? handleDelete : undefined} />
    </>
  )
}

export default VehiclesPage
