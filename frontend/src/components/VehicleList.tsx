import type { Vehicle } from '../types'

type Props = {
  vehicles: Vehicle[]
}

function VehicleList({ vehicles }: Props) {
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
        </tr>
      </thead>
      <tbody>
        {vehicles.map((vehicle) => (
          <tr key={vehicle.id}>
            <td>{vehicle.license_plate}</td>
            <td>{vehicle.brand}</td>
            <td>{vehicle.model}</td>
            <td>{new Date(vehicle.created_at).toLocaleDateString('sk-SK')}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default VehicleList
