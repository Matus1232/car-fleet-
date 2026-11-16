import { addMonths, formatDayLong, formatMonth, monthGrid, today } from '../dates'
import { dayState, freeLabel, hourLabel, isSlotPast, SLOT_HOURS, slotStyle } from '../slots'
import type { Booking } from '../types'

type Props = {
  month: string // zobrazený mesiac, napr. "2026-11"
  bookings: Booking[] | null // null = ešte sa načítavajú
  onMonthChange: (month: string) => void
  onSelectDay: (day: string) => void
}

const WEEKDAYS = ['Po', 'Ut', 'St', 'Št', 'Pi', 'So', 'Ne']

// Koľko štítkov s hodinou sa zmestí do jedného dňa. Ostatné nahradí "+2".
const MAX_CHIPS = 3

// Veľký kalendár mesiaca. Len zobrazuje: mesiac aj rezervácie dostane cez props
// a kliknutia oznamuje rodičovi (BookingsPage).
function MonthCalendar({ month, bookings, onMonthChange, onSelectDay }: Props) {
  const todayIso = today()

  // Rezervácie rozdelíme podľa dňa, aby sme pri každom políčku nemuseli prehľadávať celý zoznam.
  // Map je slovník: kľúč je deň ("2026-11-23"), hodnota zoznam rezervácií toho dňa.
  const byDay = new Map<string, Booking[]>()
  for (const booking of bookings ?? []) {
    const list = byDay.get(booking.booking_date) ?? []
    list.push(booking)
    byDay.set(booking.booking_date, list)
  }

  return (
    <section className="calendar">
      <div className="calendar-head">
        <h3>{formatMonth(month)}</h3>
        <div className="actions">
          <button className="secondary" onClick={() => onMonthChange(todayIso.slice(0, 7))}>
            Dnes
          </button>
          {/* aria-label: čítačka obrazovky by samotnú šípku nevedela zmysluplne prečítať. */}
          <button className="secondary" aria-label="Predchádzajúci mesiac" onClick={() => onMonthChange(addMonths(month, -1))}>
            ‹
          </button>
          <button className="secondary" aria-label="Ďalší mesiac" onClick={() => onMonthChange(addMonths(month, 1))}>
            ›
          </button>
        </div>
      </div>

      <div className="calendar-grid">
        {WEEKDAYS.map((name) => (
          <div key={name} className="weekday">
            {name}
          </div>
        ))}

        {monthGrid(month).map((day) => {
          const state = dayState(day)
          const outside = day.slice(0, 7) !== month // deň zo susedného mesiaca na okraji mriežky
          const dayBookings = byDay.get(day) ?? []
          // Štítok dostanú len rezervácie, o ktorých niečo vieme: moje, a adminovi všetky.
          // Cudzie obsadené termíny sa prejavia len nižším počtom voľných.
          const known = dayBookings.filter((booking) => booking.user_email !== null)
          const taken = new Set(dayBookings.map((booking) => booking.hour))
          const free = SLOT_HOURS.filter((hour) => !taken.has(hour) && !isSlotPast(day, hour)).length

          return (
            <button
              key={day}
              type="button"
              className={outside ? 'day outside' : `day ${state}`}
              // Cez víkend je zatvorené a dni susedných mesiacov patria do iného kalendára.
              disabled={outside || state === 'weekend'}
              aria-label={formatDayLong(day)}
              aria-current={day === todayIso ? 'date' : undefined}
              onClick={() => onSelectDay(day)}
            >
              <span className="day-number">{Number(day.slice(8))}</span>
              {!outside && known.length > 0 && (
                <span className="day-chips">
                  {known.slice(0, MAX_CHIPS).map((booking) => (
                    <span key={booking.id} className="chip" style={slotStyle(booking.hour)}>
                      {hourLabel(booking.hour)}
                    </span>
                  ))}
                  {known.length > MAX_CHIPS && <span className="chip-more">+{known.length - MAX_CHIPS}</span>}
                </span>
              )}
              {!outside && state === 'open' && bookings !== null && (
                <span className="day-free">{freeLabel(free)}</span>
              )}
            </button>
          )
        })}
      </div>
    </section>
  )
}

export default MonthCalendar
