import type { Vehicle } from '../types'

type Props = {
  vehicles: Vehicle[]
  onDelete?: (vehicle: Vehicle) => void // otáznik = nepovinné; keď chýba, stĺpec s tlačidlom sa neukáže
}

function VehicleList({ vehicles, onDelete }: Props) {
  if (vehicles.length === 0) {
    return <p>Zatiaľ tu nie sú žiadne autá.</p>
  }

  return (
    <table>
      <thead>
        <tr>
          <th>ŠPZ</th>
          <th>Značka</th>
          <th>Model</th>
          <th>Pridané</th>
          {onDelete && <th></th>}
        </tr>
      </thead>
      <tbody>
        {vehicles.map((vehicle) => (
          <tr key={vehicle.id}>
            <td>{vehicle.license_plate}</td>
            <td>{vehicle.brand}</td>
            <td>{vehicle.model}</td>
            <td>{new Date(vehicle.created_at).toLocaleDateString('sk-SK')}</td>
            {onDelete && (
              <td>
                <button className="secondary" onClick={() => onDelete(vehicle)}>
                  Zmazať
                </button>
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default VehicleList
