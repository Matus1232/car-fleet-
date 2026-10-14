// Tvar dát, ktoré vracia backend (zodpovedá VehicleRead v backend/app/schemas/vehicle.py).
export type Vehicle = {
  id: number
  brand: string
  model: string
  license_plate: string
  created_at: string // JSON nepozná dátum, príde ako text, napr. "2026-10-14T08:30:00Z"
}

// Čo posielame pri vytváraní auta (zodpovedá VehicleCreate). id a created_at doplní backend.
export type VehicleInput = {
  brand: string
  model: string
  license_plate: string
}

// Prihlásený používateľ z GET /auth/me (zodpovedá UserRead).
export type User = {
  id: number
  email: string
  role: 'admin' | 'driver' // rola môže byť len jeden z týchto dvoch textov
  created_at: string
}

// Odpoveď z GET /vehicles (zodpovedá VehiclePage): jedna "stránka" áut + celkový počet.
export type VehiclePage = {
  items: Vehicle[]
  total: number
  skip: number
  limit: number
}
