import type { User, Vehicle, VehicleInput, VehiclePage } from './types'

// Adresa backendu. Pri nasadení ju budeme meniť, preto je na jednom mieste.
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

// Spoločná časť všetkých požiadaviek s tokenom: pridá hlavičku a skontroluje odpoveď.
async function request(path: string, token: string, options: RequestInit = {}): Promise<Response> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { ...options.headers, Authorization: `Bearer ${token}` },
  })

  if (response.status === 401) {
    throw new UnauthorizedError()
  }
  if (!response.ok) {
    throw new Error(ERROR_MESSAGES[response.status] ?? `Požiadavka zlyhala (chyba ${response.status}).`)
  }
  return response
}

// Zrozumiteľné texty pre chyby, ktoré vracia backend (409 zatiaľ vzniká len pri duplicitnej ŠPZ).
const ERROR_MESSAGES: Record<number, string> = {
  403: 'Na túto akciu nemáš oprávnenie.',
  404: 'Auto sa nenašlo, možno ho medzitým niekto zmazal.',
  409: 'Auto s touto ŠPZ už existuje.',
  422: 'Skontroluj zadané údaje.',
}

export async function getMe(token: string): Promise<User> {
  const response = await request('/auth/me', token)
  return response.json()
}

// skip = koľko áut preskočiť, limit = koľko ich vrátiť (backend dovolí najviac 100).
export async function getVehicles(token: string, skip: number, limit: number): Promise<VehiclePage> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) })
  const response = await request(`/vehicles?${params}`, token)
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

// PATCH dovoľuje poslať len zmenené polia, my pre jednoduchosť posielame vždy všetky tri.
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
