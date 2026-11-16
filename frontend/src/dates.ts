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

// --- Kalendár ---
// Deň píšeme ako text "2026-11-23" a mesiac ako "2026-11". Texty v tomto tvare sa dajú
// porovnávať obyčajným < a >, lebo abecedné poradie je zhodné s časovým.

// Posunie deň o daný počet dní: addDays("2026-11-30", 1) -> "2026-12-01". Záporné číslo ide späť.
export function addDays(isoDate: string, days: number): string {
  const date = new Date(isoDate) // polnoc v UTC
  date.setUTCDate(date.getUTCDate() + days) // 31. + 1 Date sám prepočíta na 1. ďalšieho mesiaca
  return date.toISOString().slice(0, 10) // "2026-12-01T00:00:00.000Z" -> prvých 10 znakov
}

// Posunie mesiac: addMonths("2026-12", 1) -> "2027-01".
export function addMonths(month: string, count: number): string {
  const date = new Date(`${month}-01`)
  date.setUTCMonth(date.getUTCMonth() + count)
  return date.toISOString().slice(0, 7)
}

// Deň v týždni od pondelka: 0 = pondelok ... 6 = nedeľa.
// JavaScript ráta od nedele (0 = nedeľa), preto posun o 6 a zvyšok po delení 7.
export function weekdayIndex(isoDate: string): number {
  return (new Date(isoDate).getUTCDay() + 6) % 7
}

// Všetky dni, ktoré kalendár mesiaca ukáže: celé týždne od pondelka po nedeľu, takže na okrajoch
// je aj pár dní zo susedných mesiacov. Pre "2026-11" je to 26. 10. až 6. 12., spolu 42 dní.
export function monthGrid(month: string): string[] {
  const first = `${month}-01`
  let day = addDays(first, -weekdayIndex(first)) // pondelok týždňa, v ktorom je prvý deň mesiaca
  const days: string[] = []
  // do-while: telo prebehne aspoň raz, podmienka sa skúša až na konci.
  do {
    for (let i = 0; i < 7; i++) {
      days.push(day)
      day = addDays(day, 1)
    }
  } while (day.slice(0, 7) === month) // ďalší pondelok je ešte v tomto mesiaci -> pridaj týždeň
  return days
}

// Prvé písmeno veľké. Slovenské názvy dní a mesiacov píše prehliadač malým.
function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1)
}

// "2026-11" -> "November 2026"
export function formatMonth(month: string): string {
  const date = new Date(`${month}-01`)
  return capitalize(date.toLocaleDateString('sk-SK', { month: 'long', year: 'numeric', timeZone: 'UTC' }))
}

// "2026-11-23" -> "Pondelok 23. novembra 2026"
export function formatDayLong(isoDate: string): string {
  const text = new Date(isoDate).toLocaleDateString('sk-SK', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  })
  return capitalize(text)
}

// "2026-11-23" -> "Po 23. 11. 2026" (kratší zápis do tabuľky)
export function formatDayShort(isoDate: string): string {
  const text = new Date(isoDate).toLocaleDateString('sk-SK', {
    weekday: 'short',
    day: 'numeric',
    month: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  })
  return capitalize(text)
}

// Slovenčina má tri tvary: 1 deň, 2 až 4 dni, 5 a viac dní.
export function daysLabel(days: number): string {
  if (days === 1) return '1 deň'
  if (days >= 2 && days <= 4) return `${days} dni`
  return `${days} dní`
}
