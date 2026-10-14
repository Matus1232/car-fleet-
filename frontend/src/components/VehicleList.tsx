import type { Vehicle } from '../types'

type Props = {
  vehicles: Vehicle[]
  // Otáznik = nepovinné. Keď nedostaneme ani jedno, stĺpec s tlačidlami sa neukáže.
  onEdit?: (vehicle: Vehicle) => void
  onDelete?: (vehicle: Vehicle) => void
}

function VehicleList({ vehicles, onEdit, onDelete }: Props) {
  if (vehicles.length === 0) {
    return <p>Zatiaľ tu nie sú žiadne autá.</p>
  }

  const showActions = onEdit !== undefined || onDelete !== undefined

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ŠPZ</th>
            <th>Značka</th>
            <th>Model</th>
            <th>Pridané</th>
            {showActions && <th></th>}
          </tr>
        </thead>
        <tbody>
          {vehicles.map((vehicle) => (
            <tr key={vehicle.id}>
              <td>{vehicle.license_plate}</td>
              <td>{vehicle.brand}</td>
              <td>{vehicle.model}</td>
              <td>{new Date(vehicle.created_at).toLocaleDateString('sk-SK')}</td>
              {showActions && (
                <td>
                  <div className="actions">
                    {onEdit && (
                      <button className="secondary" onClick={() => onEdit(vehicle)}>
                        Upraviť
                      </button>
                    )}
                    {onDelete && (
                      <button className="secondary" onClick={() => onDelete(vehicle)}>
                        Zmazať
                      </button>
                    )}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default VehicleList
