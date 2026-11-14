// Tvar dát, ktoré vracia backend (zodpovedá VehicleRead v backend/app/schemas/vehicle.py).
export type Vehicle = {
  id: number
  brand: string
  model: string
  license_plate: string
  stk_valid_until: string | null // posledný deň platnosti STK, napr. "2027-05-31"; null = nezadané
  created_at: string // JSON nepozná dátum, príde ako text, napr. "2026-10-14T08:30:00Z"
}

// Čo posielame pri vytváraní auta (zodpovedá VehicleCreate). id a created_at doplní backend.
export type VehicleInput = {
  brand: string
  model: string
  license_plate: string
  stk_valid_until: string | null
}

// Čísla pre dashboard z GET /vehicles/stats (zodpovedá VehicleStats).
export type VehicleStats = {
  total: number
  stk_expiring: number // STK ešte platí, ale čoskoro skončí
  stk_expired: number // STK už neplatí
}

// Servisný záznam auta (zodpovedá ServiceRecordRead v backend/app/schemas/service_record.py).
export type ServiceRecord = {
  id: number
  vehicle_id: number
  description: string
  cost: string // suma príde ako text, napr. "89.90", aby sa nestratila presnosť
  service_date: string // len deň, napr. "2026-11-02"
  created_at: string
}

// Čo posielame pri pridávaní servisu (zodpovedá ServiceRecordCreate).
export type ServiceRecordInput = {
  description: string
  cost: string
  service_date: string
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
