import type { VehiclePage } from './types'

// Adresa backendu. Pri nasadení ju budeme meniť, preto je na jednom mieste.
const API_URL = 'http://localhost:8000'

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

// Načíta prvú stránku áut. Token posielame v hlavičke, presne ako to čaká get_current_user.
export async function getVehicles(token: string): Promise<VehiclePage> {
  const response = await fetch(`${API_URL}/vehicles`, {
    headers: { Authorization: `Bearer ${token}` },
  })

  if (response.status === 401) {
    throw new Error('Prihlásenie vypršalo, obnov stránku a prihlás sa znova.')
  }
  if (!response.ok) {
    throw new Error(`Načítanie áut zlyhalo (chyba ${response.status}).`)
  }

  return response.json()
}
