// Pravidlá rezervácií: kedy má servis otvorené a ktoré termíny sa dajú rezervovať.
// Frontend podľa nich len kreslí kalendár; skutočnú kontrolu robí backend.
import type { CSSProperties } from 'react'
import { addDays, today, weekdayIndex } from './dates'

// Termíny sú každú celú hodinu od 8:00 do 16:00 (posledný končí o 17:00) a rezervovať sa dá
// najviac 60 dní dopredu. Tie isté čísla má backend (FIRST_HOUR a LAST_HOUR
// v backend/app/models/booking.py, BOOKING_HORIZON_DAYS v backend/app/api/bookings.py),
// treba ich meniť spolu.
export const FIRST_HOUR = 8
export const LAST_HOUR = 16
export const BOOKING_HORIZON_DAYS = 60

// Hodiny všetkých termínov: [8, 9, 10, ..., 16]. Array.from vyrobí pole danej dĺžky
// a funkcia dostane poradové číslo prvku (i), z ktorého spraví hodinu.
export const SLOT_HOURS = Array.from({ length: LAST_HOUR - FIRST_HOUR + 1 }, (_, i) => FIRST_HOUR + i)

// 9 -> "9:00"
export function hourLabel(hour: number): string {
  return `${hour}:00`
}

// 9 -> "9:00 – 10:00"
export function slotLabel(hour: number): string {
  return `${hourLabel(hour)} – ${hourLabel(hour + 1)}`
}

// Každá hodina má vlastnú pastelovú farbu. Tu je len jej odtieň (uhol na farebnom kruhu
// v stupňoch); svetlosť a sýtosť sú pre všetky rovnaké a určuje ich index.css cez oklch().
// Ráno začína teplou žltou, cez deň prejde zelenou a modrou a poobede končí ružovou.
const SLOT_HUES = [95, 130, 165, 200, 235, 270, 305, 345, 30]

// Farbu posielame do CSS ako premennú --hue. TypeScript vlastné CSS premenné v type
// CSSProperties nepozná, preto mu cez "as" povieme, že objekt je v poriadku.
export function slotStyle(hour: number): CSSProperties {
  return { '--hue': SLOT_HUES[hour - FIRST_HOUR] } as CSSProperties
}

// Prečo sa v daný deň (ne)dá rezervovať.
export type DayState = 'open' | 'weekend' | 'past' | 'far'

export function dayState(day: string): DayState {
  if (weekdayIndex(day) >= 5) return 'weekend' // 5 = sobota, 6 = nedeľa
  // Dnešok sa ráta ako minulý, keď už začal aj posledný termín dňa.
  if (isSlotPast(day, LAST_HOUR)) return 'past'
  if (day > addDays(today(), BOOKING_HORIZON_DAYS)) return 'far'
  return 'open'
}

// Termín sa nedá rezervovať, keď už začal: o 10:30 je preč aj termín o 10:00.
export function isSlotPast(day: string, hour: number): boolean {
  const now = today()
  if (day !== now) return day < now
  return hour <= new Date().getHours()
}

// Slovenčina má tri tvary: 1 voľný, 2 až 4 voľné, 5 a viac voľných.
export function freeLabel(count: number): string {
  if (count === 0) return 'obsadené'
  if (count === 1) return '1 voľný'
  if (count <= 4) return `${count} voľné`
  return `${count} voľných`
}
