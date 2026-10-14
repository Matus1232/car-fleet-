// Tvar dát, ktoré vracia backend (zodpovedá VehicleRead v backend/app/schemas/vehicle.py).
export type Vehicle = {
  id: number
  brand: string
  model: string
  license_plate: string
  created_at: string // JSON nepozná dátum, príde ako text, napr. "2026-10-14T08:30:00Z"
}
