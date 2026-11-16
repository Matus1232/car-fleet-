import { useState } from 'react'
import type { FormEvent } from 'react'
import { createBooking, deleteBooking, errorMessage, UnauthorizedError } from '../api'
import { addDays, formatDayLong, weekdayIndex } from '../dates'
import { BOOKING_HORIZON_DAYS, dayState, isSlotPast, SLOT_HOURS, slotLabel, slotStyle } from '../slots'
import type { Booking } from '../types'

type Props = {
  token: string
  day: string // otvorený deň, napr. "2026-11-23"
  bookings: Booking[] | null // rezervácie zobrazeného mesiaca; null = ešte sa načítavajú
  onBack: () => void // späť na kalendár mesiaca
  onSelectDay: (day: string) => void
  onChanged: () => void // pribudla alebo zmizla rezervácia -> rodič načíta dáta znova
  onUnauthorized: () => void
}

// Najbližší pracovný deň v danom smere (1 = dopredu, -1 = dozadu). Víkendy preskočí.
function nextWorkday(day: string, step: 1 | -1): string {
  let next = addDays(day, step)
  while (weekdayIndex(next) >= 5) next = addDays(next, step)
  return next
}

// Jeden deň rozdelený na hodinové termíny. Voľný termín je farebné tlačidlo; po kliknutí
// sa pod termínmi objaví formulár na potvrdenie rezervácie.
function DaySlots({ token, day, bookings, onBack, onSelectDay, onChanged, onUnauthorized }: Props) {
  const [selectedHour, setSelectedHour] = useState<number | null>(null)
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const state = dayState(day)
  // Rezervácie tohto dňa podľa hodiny: byHour.get(10) je rezervácia o 10:00 alebo undefined.
  const byHour = new Map<number, Booking>()
  for (const booking of bookings ?? []) {
    if (booking.booking_date === day) byHour.set(booking.hour, booking)
  }

  function handleError(err: unknown) {
    if (err instanceof UnauthorizedError) {
      onUnauthorized()
      return
    }
    setError(errorMessage(err))
    // Chyba často znamená, že naše dáta sú staré (termín medzitým obsadil niekto iný),
    // preto si ich vypýtame znova.
    onChanged()
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (selectedHour === null) return

    setError(null)
    setSaving(true)
    try {
      await createBooking(token, { booking_date: day, hour: selectedHour, note })
      setSelectedHour(null)
      setNote('')
      onChanged()
    } catch (err) {
      setSelectedHour(null)
      handleError(err)
    } finally {
      setSaving(false)
    }
  }

  async function handleCancel(booking: Booking) {
    if (!confirm(`Naozaj zrušiť rezerváciu o ${slotLabel(booking.hour)}?`)) return

    setError(null)
    try {
      await deleteBooking(token, booking.id)
      onChanged()
    } catch (err) {
      handleError(err)
    }
  }

  // Čo sa zobrazí v jednom termíne. Poradie podmienok je dôležité: najprv rezervácia
  // (aj minulú chceme vidieť), až potom dôvody, prečo sa voľný termín nedá rezervovať.
  function renderSlot(hour: number) {
    const booking = byHour.get(hour)
    const past = isSlotPast(day, hour)
    const time = <span className="slot-time">{slotLabel(hour)}</span>

    if (booking && booking.user_email !== null) {
      // Moja rezervácia, alebo cudzia v očiach admina (ten vidí e-mail aj poznámku).
      return (
        <div key={hour} className="slot booked" style={slotStyle(hour)}>
          {time}
          <span className="slot-status">{booking.mine ? 'Tvoj termín' : booking.user_email}</span>
          {booking.note && <span className="slot-note">{booking.note}</span>}
          {!past && (
            <button className="ghost danger" onClick={() => handleCancel(booking)}>
              Zrušiť rezerváciu
            </button>
          )}
        </div>
      )
    }
    if (booking) {
      return (
        <div key={hour} className="slot taken">
          {time}
          <span className="slot-status">Obsadené</span>
        </div>
      )
    }
    if (past || state !== 'open') {
      return (
        <div key={hour} className="slot closed">
          {time}
          <span className="slot-status">{past ? 'Už prebehlo' : 'Nedá sa rezervovať'}</span>
        </div>
      )
    }
    return (
      // aria-pressed: čítačka obrazovky povie, ktorý termín je vybraný; CSS podľa neho kreslí rámik.
      <button
        key={hour}
        type="button"
        className="slot free"
        style={slotStyle(hour)}
        aria-pressed={selectedHour === hour}
        onClick={() => setSelectedHour(hour)}
      >
        {time}
        <span className="slot-status">{selectedHour === hour ? 'Vybraný termín' : 'Voľné'}</span>
      </button>
    )
  }

  return (
    <section className="calendar">
      <div className="calendar-head">
        <h3>{formatDayLong(day)}</h3>
        <div className="actions">
          <button className="secondary" onClick={onBack}>
            ← Kalendár
          </button>
          <button className="secondary" aria-label="Predchádzajúci deň" onClick={() => onSelectDay(nextWorkday(day, -1))}>
            ‹
          </button>
          <button className="secondary" aria-label="Ďalší deň" onClick={() => onSelectDay(nextWorkday(day, 1))}>
            ›
          </button>
        </div>
      </div>

      <div className="day-body">
        {error && <p className="error">{error}</p>}
        {state === 'far' && (
          <p className="hint">Rezervovať sa dá najviac {BOOKING_HORIZON_DAYS} dní dopredu.</p>
        )}

        {bookings === null ? (
          <p className="loading">Načítavam…</p>
        ) : (
          <div className="slots">{SLOT_HOURS.map(renderSlot)}</div>
        )}

        {selectedHour !== null && (
          <form className="booking-form" onSubmit={handleSubmit}>
            <label className="grow">
              Poznámka pre servis (nepovinné)
              <input
                value={note}
                onChange={(e) => setNote(e.target.value)}
                maxLength={200}
                placeholder="napr. Octavia BA123AB, výmena oleja"
                autoFocus
              />
            </label>
            <button type="submit" disabled={saving}>
              {saving ? 'Rezervujem…' : `Rezervovať ${slotLabel(selectedHour)}`}
            </button>
            <button type="button" className="secondary" onClick={() => setSelectedHour(null)}>
              Zrušiť
            </button>
          </form>
        )}
      </div>
    </section>
  )
}

export default DaySlots
