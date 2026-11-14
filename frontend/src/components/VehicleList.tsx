import { daysLabel, daysUntil, formatDate, STK_SOON_DAYS } from '../dates'
import type { Vehicle } from '../types'

type Props = {
  vehicles: Vehicle[]
  onServices: (vehicle: Vehicle) => void // servis si smie pozrieť každý, preto je povinné
  // Otáznik = nepovinné. Keď ich nedostaneme, tlačidlá Upraviť a Zmazať sa neukážu.
  onEdit?: (vehicle: Vehicle) => void
  onDelete?: (vehicle: Vehicle) => void
}

// Bunka so STK: dátum a pri končiacej alebo neplatnej STK aj malý štítok.
function StkCell({ validUntil }: { validUntil: string | null }) {
  if (validUntil === null) return <span className="date">–</span>

  const days = daysUntil(validUntil)
  return (
    <>
      <span className="date">{formatDate(validUntil)}</span>
      {days < 0 && <span className="badge alert">po termíne</span>}
      {days >= 0 && days <= STK_SOON_DAYS && (
        <span className="badge">{days === 0 ? 'končí dnes' : `o ${daysLabel(days)}`}</span>
      )}
    </>
  )
}

function VehicleList({ vehicles, onServices, onEdit, onDelete }: Props) {
  if (vehicles.length === 0) {
    return <p className="empty">Zatiaľ tu nie sú žiadne autá.</p>
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ŠPZ</th>
            <th>Značka</th>
            <th>Model</th>
            <th>STK do</th>
            <th>Pridané</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {vehicles.map((vehicle) => (
            <tr key={vehicle.id}>
              <td>
                <span className="plate">{vehicle.license_plate}</span>
              </td>
              <td>{vehicle.brand}</td>
              <td>{vehicle.model}</td>
              <td>
                <StkCell validUntil={vehicle.stk_valid_until} />
              </td>
              <td className="date">{new Date(vehicle.created_at).toLocaleDateString('sk-SK')}</td>
              <td className="actions-cell">
                <div className="actions">
                  <button className="ghost" onClick={() => onServices(vehicle)}>
                    Servis
                  </button>
                  {onEdit && (
                    <button className="ghost" onClick={() => onEdit(vehicle)}>
                      Upraviť
                    </button>
                  )}
                  {onDelete && (
                    <button className="ghost danger" onClick={() => onDelete(vehicle)}>
                      Zmazať
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default VehicleList
