import type {
  Booking,
  BookingInput,
  ServiceRecord,
  ServiceRecordInput,
  StkFilter,
  User,
  Vehicle,
  VehicleInput,
  VehiclePage,
  VehicleStats,
} from './types'

// Adresa backendu. Prehliadač ju volá priamo, aj keď frontend beží v Dockeri (port 8000 je zverejnený).
const API_URL = 'http://localhost:8000'

// Vlastný typ chyby pre 401: podľa neho stránka pozná, že treba používateľa odhlásiť.
export class UnauthorizedError extends Error {}

// Zo zachytenej chyby spraví text pre používateľa.
export function errorMessage(err: unknown): string {
  // fetch hodí TypeError, keď sa na server vôbec nedá pripojiť (napr. nebeží Docker).
  if (err instanceof TypeError) return 'Server je nedostupný.'
  if (err instanceof Error) return err.message
  return 'Nastala neznáma chyba.'
}

// Pošle email a heslo na POST /auth/token a vráti JWT token.
export async function login(email: string, password: string): Promise<string> {
  const response = await fetch(`${API_URL}/auth/token`, {
    method: 'POST',
    // OAuth2 štandard chce formulár (nie JSON) a pole sa volá 'username', aj keď je to email.
    body: new URLSearchParams({ username: email, password }),
  })

  if (response.status === 401) {
    throw new Error('Nesprávny e-mail alebo heslo.')
  }
  if (!response.ok) {
    throw new Error(`Prihlásenie zlyhalo (chyba ${response.status}).`)
  }

  const data: { access_token: string } = await response.json()
  return data.access_token
}

// Vytvorí nový účet cez POST /auth/register. Token nevracia, po registrácii sa treba prihlásiť.
export async function register(email: string, password: string): Promise<void> {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    // Na rozdiel od prihlásenia je toto bežný JSON endpoint, nie OAuth2 formulár.
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })

  if (!response.ok) {
    throw new Error(REGISTER_ERRORS[response.status] ?? `Registrácia zlyhala (chyba ${response.status}).`)
  }
}

const REGISTER_ERRORS: Record<number, string> = {
  409: 'Účet s týmto e-mailom už existuje.',
  422: 'Zadaj platný e-mail a heslo s aspoň 8 znakmi.',
  429: 'Príliš veľa registrácií naraz, skús to neskôr.',
}

// Spoločná časť všetkých požiadaviek s tokenom: pridá hlavičku a skontroluje odpoveď.
// messages = vlastné texty chýb pre konkrétnu časť aplikácie; majú prednosť pred všeobecnými.
async function request(
  path: string,
  token: string,
  options: RequestInit = {},
  messages: Record<number, string> = {},
): Promise<Response> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { ...options.headers, Authorization: `Bearer ${token}` },
  })

  if (response.status === 401) {
    throw new UnauthorizedError()
  }
  if (!response.ok) {
    throw new Error(
      messages[response.status] ??
        ERROR_MESSAGES[response.status] ??
        `Požiadavka zlyhala (chyba ${response.status}).`,
    )
  }
  return response
}

// Zrozumiteľné texty pre chyby, ktoré vracia backend (409 zatiaľ vzniká len pri duplicitnej ŠPZ).
const ERROR_MESSAGES: Record<number, string> = {
  403: 'Na túto akciu nemáš oprávnenie.',
  404: 'Záznam sa nenašiel, možno ho medzitým niekto zmazal.',
  409: 'Auto s touto ŠPZ už existuje.',
  422: 'Skontroluj zadané údaje.',
}

export async function getMe(token: string): Promise<User> {
  const response = await request('/auth/me', token)
  return response.json()
}

// skip = koľko áut preskočiť, limit = koľko ich vrátiť (backend dovolí najviac 100).
// stk = nepovinný filter podľa stavu STK; null = všetky autá.
export async function getVehicles(
  token: string,
  skip: number,
  limit: number,
  stk: StkFilter | null = null,
): Promise<VehiclePage> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) })
  if (stk !== null) params.set('stk', stk) // pridá do adresy &stk=expired
  const response = await request(`/vehicles?${params}`, token)
  return response.json()
}

// Počty pre dashboard: všetky autá, autá s končiacou STK a autá po STK.
export async function getVehicleStats(token: string): Promise<VehicleStats> {
  const response = await request('/vehicles/stats', token)
  return response.json()
}

export async function createVehicle(token: string, data: VehicleInput): Promise<Vehicle> {
  const response = await request('/vehicles', token, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return response.json()
}

// PATCH dovoľuje poslať len zmenené polia, my pre jednoduchosť posielame vždy všetky.
export async function updateVehicle(token: string, id: number, data: VehicleInput): Promise<Vehicle> {
  const response = await request(`/vehicles/${id}`, token, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return response.json()
}

// DELETE vracia 204 No Content, takže z odpovede nič nečítame.
export async function deleteVehicle(token: string, id: number): Promise<void> {
  await request(`/vehicles/${id}`, token, { method: 'DELETE' })
}

// Servisné záznamy sú na backende "pod" autom: /vehicles/5/services.
export async function getServices(token: string, vehicleId: number): Promise<ServiceRecord[]> {
  const response = await request(`/vehicles/${vehicleId}/services`, token)
  return response.json()
}

export async function createService(
  token: string,
  vehicleId: number,
  data: ServiceRecordInput,
): Promise<ServiceRecord> {
  const response = await request(`/vehicles/${vehicleId}/services`, token, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return response.json()
}

export async function deleteService(token: string, vehicleId: number, serviceId: number): Promise<void> {
  await request(`/vehicles/${vehicleId}/services/${serviceId}`, token, { method: 'DELETE' })
}

// Rezervácie termínov servisu. Tie isté kódy chýb tu znamenajú niečo iné než pri autách
// (409 = obsadený termín, nie duplicitná ŠPZ), preto majú vlastné texty.
const BOOKING_ERRORS: Record<number, string> = {
  403: 'Zrušiť môžeš len svoju rezerváciu.',
  404: 'Táto rezervácia už neexistuje.',
  409: 'Tento termín si práve rezervoval niekto iný.',
  422: 'Tento termín sa už nedá rezervovať.',
}

// Obsadené termíny od dňa start po deň end (vrátane), napr. "2026-11-01" až "2026-11-30".
export async function getBookings(token: string, start: string, end: string): Promise<Booking[]> {
  const params = new URLSearchParams({ start, end })
  const response = await request(`/bookings?${params}`, token, {}, BOOKING_ERRORS)
  return response.json()
}

export async function createBooking(token: string, data: BookingInput): Promise<Booking> {
  const response = await request(
    '/bookings',
    token,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    },
    BOOKING_ERRORS,
  )
  return response.json()
}

export async function deleteBooking(token: string, id: number): Promise<void> {
  await request(`/bookings/${id}`, token, { method: 'DELETE' }, BOOKING_ERRORS)
}
