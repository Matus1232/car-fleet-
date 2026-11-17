import { Link } from 'react-router'

// Jedna položka cenníka. from = true znamená "od": konečná cena závisí od auta alebo dielov.
type PriceItem = {
  name: string
  detail: string
  price: number
  from?: boolean
}

// Cenník je zatiaľ napevno vo frontende. Mení sa zriedka a nikto ho neupravuje v aplikácii,
// takže tabuľka v databáze a endpoint by boli zbytočná práca navyše. Keby ho mal meniť admin
// cez obrazovku, presunul by sa na backend rovnako ako autá.
const PRICES: PriceItem[] = [
  { name: 'Výmena oleja a filtra', detail: 'olej, olejový filter, kontrola kvapalín', price: 59, from: true },
  { name: 'Diagnostika', detail: 'načítanie chýb z riadiacej jednotky a vyhodnotenie', price: 35 },
  { name: 'Kontrola pred STK', detail: 'svetlá, brzdy, tlmiče, pneumatiky, výfuk', price: 25 },
  { name: 'Výmena brzdových platničiek', detail: 'jedna náprava, bez ceny platničiek', price: 45, from: true },
  { name: 'Prezutie pneumatík', detail: '4 kolesá vrátane vyváženia', price: 40 },
  { name: 'Geometria', detail: 'nastavenie zbiehavosti a odklonu kolies', price: 45 },
  { name: 'Servis klimatizácie', detail: 'dezinfekcia, kontrola tesnosti, doplnenie chladiva', price: 69 },
]

// Formátovač vytvoríme raz, mimo komponentu: 59 -> "59,00 €".
const money = new Intl.NumberFormat('sk-SK', { style: 'currency', currency: 'EUR' })

function PriceListPage() {
  return (
    <>
      <div className="toolbar">
        <h2>Cenník</h2>
        {/* Link vyzerá ako tlačidlo, ale je to odkaz: vedie na inú stránku, nič neodosiela. */}
        <Link className="button-link" to="/bookings">
          Rezervovať termín
        </Link>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Služba</th>
              <th>Čo zahŕňa</th>
              <th className="num">Cena</th>
            </tr>
          </thead>
          <tbody>
            {PRICES.map((item) => (
              <tr key={item.name}>
                <td className="strong">{item.name}</td>
                <td className="wrap muted">{item.detail}</td>
                <td className="num">
                  {item.from && <span className="muted">od </span>}
                  {money.format(item.price)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="footnote">
        Ceny sú orientačné a vrátane DPH. Náhradné diely sa účtujú zvlášť, presnú cenu povieme pri obhliadke auta.
      </p>
    </>
  )
}

export default PriceListPage
