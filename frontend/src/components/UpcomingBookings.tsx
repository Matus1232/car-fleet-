import { useEffect, useState } from 'react'
import { deleteBooking, errorMessage, getBookings, UnauthorizedError } from '../api'
import { addDays, formatDayLong, formatDayShort, today } from '../dates'
import { BOOKING_HORIZON_DAYS, hourLabel, isSlotPast, slotLabel, slotStyle } from '../slots'
import type { Booking } from '../types'

type Props = {
  token: string
  isAdmin: boolean
  // Číslo, ktoré rodič zvýši po každej zmene rezervácií (rovnaký trik ako pri Dashboarde).
  version: number
  onSelectDay: (day: string) => void
  onChanged: () => void
  onUnauthorized: () => void
}

// Zoznam pod kalendárom. Bežný používateľ v ňom vidí svoje najbližšie rezervácie,
// admin rezervácie všetkých ľudí aj s e-mailom.
function UpcomingBookings({ token, isAdmin, version, onSelectDay, onChanged, onUnauthorized }: Props) {
  const [bookings, setBookings] = useState<Booking[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let ignore = false
    // Ďalej než BOOKING_HORIZON_DAYS sa rezervovať nedá, takže toto obdobie pokryje všetko budúce.
    const start = today()

    getBookings(token, start, addDays(start, BOOKING_HORIZON_DAYS))
      .then((data) => {
        if (!ignore) setBookings(data)
      })
      .catch((err) => {
        // Iné chyby tu neriešime, ukáže ich kalendár nad zoznamom (pýta sa na to isté API).
        if (!ignore && err instanceof UnauthorizedError) onUnauthorized()
      })

    return () => {
      ignore = true
    }
  }, [token, version, onUnauthorized])

  async function handleCancel(booking: Booking) {
    if (!confirm(`Naozaj zrušiť rezerváciu ${formatDayLong(booking.booking_date)} o ${hourLabel(booking.hour)}?`)) {
      return
    }

    setError(null)
    try {
      await deleteBooking(token, booking.id)
    } catch (err) {
      if (err instanceof UnauthorizedError) {
        onUnauthorized()
        return
      }
      setError(errorMessage(err))
    }
    onChanged() // aj po chybe: rezervácia možno medzitým zmizla, nech sa zoznam obnoví
  }

  if (bookings === null) return null // kým dáta neprišli, pod kalendárom nie je nič

  // Server vracia všetky obsadené termíny. Admin chce vidieť všetky, ostatní len svoje.
  // Dnešné termíny, ktoré už začali, vynecháme.
  const items = bookings.filter(
    (booking) => (isAdmin || booking.mine) && !isSlotPast(booking.booking_date, booking.hour),
  )

  return (
    <section className="upcoming">
      <div className="toolbar">
        <h2>
          {isAdmin ? 'Najbližšie rezervácie' : 'Moje rezervácie'}
          <span className="count">{items.length}</span>
        </h2>
      </div>

      {error && <p className="error">{error}</p>}

      {items.length === 0 ? (
        <p className="empty">
          {isAdmin ? 'Zatiaľ si nikto nerezervoval termín.' : 'Zatiaľ nemáš rezervovaný žiadny termín.'}
        </p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Deň</th>
                <th>Čas</th>
                {isAdmin && <th>Kto</th>}
                <th>Poznámka</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((booking) => (
                <tr key={booking.id}>
                  <td className="date">{formatDayShort(booking.booking_date)}</td>
                  <td>
                    <span className="chip" style={slotStyle(booking.hour)}>
                      {slotLabel(booking.hour)}
                    </span>
                  </td>
                  {isAdmin && <td>{booking.mine ? 'ja' : booking.user_email}</td>}
                  <td className="wrap">{booking.note ?? <span className="date">–</span>}</td>
                  <td className="actions-cell">
                    <div className="actions">
                      <button className="ghost" onClick={() => onSelectDay(booking.booking_date)}>
                        Otvoriť deň
                      </button>
                      <button className="ghost danger" onClick={() => handleCancel(booking)}>
                        Zrušiť
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default UpcomingBookings
