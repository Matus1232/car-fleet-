import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { createService, deleteService, errorMessage, getServices, UnauthorizedError } from '../api'
import type { ServiceRecord, Vehicle } from '../types'

type Props = {
  token: string
  vehicle: Vehicle
  isAdmin: boolean
  onClose: () => void
  onUnauthorized: () => void
}

// Formátovač vytvoríme raz, mimo komponentu: 89.9 -> "89,90 €".
const money = new Intl.NumberFormat('sk-SK', { style: 'currency', currency: 'EUR' })

// Dnešný dátum v tvare "2026-11-14", aký chce <input type="date"> aj backend.
function today(): string {
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0') // 5 -> "05"
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}` // mesiace sú od 0
}

// "2026-11-02" -> "2. 11. 2026". timeZone: 'UTC', aby sa deň neposunul podľa časového pásma.
function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString('sk-SK', { timeZone: 'UTC' })
}

function VehicleServices({ token, vehicle, isAdmin, onClose, onUnauthorized }: Props) {
  const [records, setRecords] = useState<ServiceRecord[] | null>(null) // null = ešte sa načítava
  const [error, setError] = useState<string | null>(null)
  const [serviceDate, setServiceDate] = useState(today)
  const [description, setDescription] = useState('')
  const [cost, setCost] = useState('')
  const [saving, setSaving] = useState(false)

  function handleError(err: unknown) {
    if (err instanceof UnauthorizedError) {
      onUnauthorized()
    } else {
      setError(errorMessage(err))
    }
  }

  // Po otvorení panela načítame záznamy tohto auta.
  useEffect(() => {
    let ignore = false

    getServices(token, vehicle.id)
      .then((data) => {
        if (!ignore) setRecords(data)
      })
      .catch((err) => {
        if (ignore) return
        if (err instanceof UnauthorizedError) {
          onUnauthorized()
        } else {
          setError(errorMessage(err))
        }
      })

    return () => {
      ignore = true
    }
  }, [token, vehicle.id, onUnauthorized])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSaving(true)
    try {
      // Cenu posielame ako text ("89.90"), nie ako číslo: backend z nej spraví presný Decimal.
      await createService(token, vehicle.id, { description, cost, service_date: serviceDate })
      // Zoznam si vypýtame znova, takže poradie aj zaokrúhlenie určí backend.
      setRecords(await getServices(token, vehicle.id))
      setDescription('')
      setCost('')
    } catch (err) {
      handleError(err)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(record: ServiceRecord) {
    if (!confirm(`Naozaj zmazať záznam „${record.description}“?`)) return

    setError(null)
    try {
      await deleteService(token, vehicle.id, record.id)
      setRecords(await getServices(token, vehicle.id))
    } catch (err) {
      handleError(err)
    }
  }

  // reduce prejde všetky záznamy a postupne sčíta ceny; začína od 0.
  const total = (records ?? []).reduce((sum, record) => sum + Number(record.cost), 0)

  return (
    <section className="card wide">
      <div className="toolbar">
        <h2>
          Servis <span className="plate">{vehicle.license_plate}</span>
          <span className="count">
            {vehicle.brand} {vehicle.model}
          </span>
        </h2>
        <button className="secondary" onClick={onClose}>
          Zavrieť
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {records === null ? (
        error === null && <p className="loading">Načítavam…</p>
      ) : records.length === 0 ? (
        <p className="empty">Toto auto zatiaľ nemá žiadny servisný záznam.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Dátum</th>
                <th>Čo sa robilo</th>
                <th className="num">Cena</th>
                {isAdmin && <th></th>}
              </tr>
            </thead>
            <tbody>
              {records.map((record) => (
                <tr key={record.id}>
                  <td className="date">{formatDate(record.service_date)}</td>
                  <td className="wrap">{record.description}</td>
                  <td className="num">{money.format(Number(record.cost))}</td>
                  {isAdmin && (
                    <td className="actions-cell">
                      <div className="actions">
                        <button className="ghost danger" onClick={() => handleDelete(record)}>
                          Zmazať
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan={2}>Spolu</td>
                <td className="num">{money.format(total)}</td>
                {isAdmin && <td></td>}
              </tr>
            </tfoot>
          </table>
        </div>
      )}

      {isAdmin && (
        <form className="service-form" onSubmit={handleSubmit}>
          <label>
            Dátum
            <input type="date" value={serviceDate} onChange={(e) => setServiceDate(e.target.value)} required />
          </label>

          <label className="grow">
            Čo sa robilo
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              maxLength={500}
              placeholder="napr. výmena oleja"
            />
          </label>

          <label>
            Cena (€)
            {/* step="0.01" dovolí centy, min a max sú rovnaké hranice ako na backende. */}
            <input
              type="number"
              value={cost}
              onChange={(e) => setCost(e.target.value)}
              required
              min="0"
              max="99999999.99"
              step="0.01"
              placeholder="0,00"
            />
          </label>

          <button type="submit" disabled={saving}>
            {saving ? 'Ukladám…' : 'Pridať záznam'}
          </button>
        </form>
      )}
    </section>
  )
}

export default VehicleServices
