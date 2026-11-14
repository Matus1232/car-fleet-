// Pomocné funkcie na prácu s dátumami. Backend posiela deň ako text "2026-11-14".

// Koľko dní pred koncom platnosti sa STK ráta ako "čoskoro končí".
// To isté číslo má backend (STK_SOON_DAYS v backend/app/api/vehicles.py), treba ich meniť spolu.
export const STK_SOON_DAYS = 30

const MS_PER_DAY = 24 * 60 * 60 * 1000 // milisekúnd v jednom dni

// Dnešný dátum v tvare "2026-11-14", aký chce <input type="date"> aj backend.
export function today(): string {
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0') // 5 -> "05"
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}` // mesiace sú od 0
}

// "2026-11-02" -> "2. 11. 2026". timeZone: 'UTC', aby sa deň neposunul podľa časového pásma.
export function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString('sk-SK', { timeZone: 'UTC' })
}

// Koľko dní ostáva do daného dňa: 0 = dnes, 5 = o päť dní, -3 = pred tromi dňami.
// new Date("2026-11-14") je polnoc v UTC, takže rozdiel dvoch dní je vždy celý násobok dňa.
export function daysUntil(isoDate: string): number {
  return Math.round((new Date(isoDate).getTime() - new Date(today()).getTime()) / MS_PER_DAY)
}

// Slovenčina má tri tvary: 1 deň, 2 až 4 dni, 5 a viac dní.
export function daysLabel(days: number): string {
  if (days === 1) return '1 deň'
  if (days >= 2 && days <= 4) return `${days} dni`
  return `${days} dní`
}
