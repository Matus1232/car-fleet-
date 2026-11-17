import { useEffect, useState } from 'react'
import { errorMessage, getBookings, UnauthorizedError } from '../api'
import { monthGrid, today } from '../dates'
import type { Booking } from '../types'
import DaySlots from './DaySlots'
import MonthCalendar from './MonthCalendar'
import UpcomingBookings from './UpcomingBookings'

type Props = {
  isAdmin: boolean
  onUnauthorized: () => void
}

// Stránka s rezerváciami: veľký kalendár mesiaca, po kliknutí na deň hodinové termíny
// toho dňa a pod tým zoznam najbližších rezervácií.
function BookingsPage({ isAdmin, onUnauthorized }: Props) {
  // Zobrazený mesiac ako text "2026-11". today() vráti "2026-11-16", prvých 7 znakov je mesiac.
  const [month, setMonth] = useState(() => today().slice(0, 7))
  // Otvorený deň ("2026-11-23"); null = je vidieť kalendár celého mesiaca.
  const [selectedDay, setSelectedDay] = useState<string | null>(null)
  // K načítaným rezerváciám si pamätáme aj mesiac, ku ktorému patria. Po prepnutí mesiaca
  // tak vieme, že staré dáta už neplatia, a neukážeme pri nových dňoch nesprávne počty.
  const [loaded, setLoaded] = useState<{ month: string; items: Booking[] } | null>(null)
  const [error, setError] = useState<string | null>(null)
  // Počítadlo, ktoré zvýšime po každej rezervácii alebo zrušení. Je v závislostiach useEffect
  // (tu aj v UpcomingBookings), takže jeho zmena = načítaj znova.
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let ignore = false
    // Pýtame si celú mriežku kalendára, teda aj pár dní zo susedných mesiacov na okrajoch.
    const days = monthGrid(month)

    getBookings(days[0], days[days.length - 1])
      .then((items) => {
        if (ignore) return
        setLoaded({ month, items })
        setError(null)
      })
      .catch((err) => {
        if (ignore) return
        if (err instanceof UnauthorizedError) {
          onUnauthorized()
        } else {
          setError(errorMessage(err))
        }
      })

    return () => {
      ignore = true
    }
  }, [month, version, onUnauthorized])

  function reload() {
    setVersion((count) => count + 1)
  }

  // Deň sa dá otvoriť z kalendára, zo zoznamu rezervácií aj šípkami v dennom pohľade.
  // Mesiac prepneme spolu s ním, aby sa načítali rezervácie správneho obdobia.
  function openDay(day: string) {
    setSelectedDay(day)
    setMonth(day.slice(0, 7))
  }

  // null = rezervácie zobrazeného mesiaca ešte neprišli.
  const bookings = loaded?.month === month ? loaded.items : null

  return (
    <>
      <div className="toolbar">
        <h2>{isAdmin ? 'Rezervácie servisu' : 'Termín servisu'}</h2>
      </div>

      {error && (
        <div className="error">
          <p>{error}</p>
          <button onClick={reload}>Skúsiť znova</button>
        </div>
      )}

      {selectedDay === null ? (
        <MonthCalendar month={month} bookings={bookings} onMonthChange={setMonth} onSelectDay={openDay} />
      ) : (
        // key: pri prechode na iný deň sa panel vytvorí nanovo, takže zabudne vybranú hodinu
        // a rozpísanú poznámku z predošlého dňa.
        <DaySlots
          key={selectedDay}
          day={selectedDay}
          bookings={bookings}
          onBack={() => setSelectedDay(null)}
          onSelectDay={openDay}
          onChanged={reload}
          onUnauthorized={onUnauthorized}
        />
      )}

      <UpcomingBookings
        isAdmin={isAdmin}
        version={version}
        onSelectDay={openDay}
        onChanged={reload}
        onUnauthorized={onUnauthorized}
      />
    </>
  )
}

export default BookingsPage
