# Frontend

React + TypeScript aplikácia postavená na Vite. Prehľad celého projektu je v [hlavnom README](../README.md).

V Dockeri ju spúšťa `Dockerfile` v tomto priečinku: vo vývoji fáza `dev` (Vite dev server),
v produkcii posledná fáza, kde hotový build posiela nginx podľa `nginx.conf` (šablóna: `/api` posiela
na backend, presmeruje na HTTPS a pridá bezpečnostné hlavičky). Pri vývoji posiela `/api` ďalej Vite
(`vite.config.ts`).

## Súbory v `src/`

```
main.tsx                  vstupný bod: vykreslí App do <div id="root"> v index.html
App.tsx                   prihlásený používateľ (z GET /auth/me), hlavička, stránky (React Router)
api.ts                    všetka komunikácia s backendom cez /api (fetch, hlavička proti CSRF, texty chýb)
types.ts                  TypeScript typy zodpovedajúce schémam backendu (Vehicle, User, ...)
dates.ts                  pomocné funkcie na dátumy (dnešok, formátovanie, dni do termínu, mriežka mesiaca)
slots.ts                  pravidlá rezervácií: otváracie hodiny, čo je minulosť, farba termínu
index.css                 všetky štýly
assets/car-outline.svg    sivý obrys auta na pozadí dashboardu a karty v menu
assets/calendar-outline.svg  sivý obrys kalendára na karte v menu
assets/receipt-outline.svg   sivý obrys bločku na karte Cenník
assets/cart-outline.svg      sivý obrys košíka na karte E-shop a na stránke e-shopu
components/
  LoginForm.tsx           prihlasovací formulár
  RegisterForm.tsx        registrácia nového účtu, po nej rovno prihlási
  HomePage.tsx            úvodná stránka: privítanie a menu (Vozový park, Termín servisu)
  BookingsPage.tsx        stránka s rezerváciami: načítanie, zobrazený mesiac a otvorený deň
  MonthCalendar.tsx       veľký kalendár mesiaca (len zobrazuje, dáta dostane cez props)
  DaySlots.tsx            hodinové termíny jedného dňa: rezervácia a zrušenie
  UpcomingBookings.tsx    zoznam najbližších rezervácií pod kalendárom
  PriceListPage.tsx       cenník servisných úkonov (ceny sú napevno v súbore)
  ShopPage.tsx            e-shop, zatiaľ len oznam „pripravujeme“
  VehiclesPage.tsx        stránka s autami: načítanie, stránkovanie, pridanie, úprava, mazanie
  Dashboard.tsx           prehľad hore: počet áut, končiaca STK, autá po STK
  VehicleList.tsx         tabuľka áut (len zobrazuje, dáta dostane cez props)
  VehicleForm.tsx         formulár na pridanie aj úpravu auta
  VehicleServices.tsx     servisné záznamy jedného auta: zoznam, súčet a formulár na pridanie
  Pagination.tsx          tlačidlá Predchádzajúca / Ďalšia
```

## Komponenty

```mermaid
flowchart TD
    main["main.tsx"] --> App
    App --> LoginForm
    App --> RegisterForm
    App --> HomePage
    App --> VehiclesPage
    App --> BookingsPage
    App --> PriceListPage
    App --> ShopPage
    VehiclesPage --> Dashboard
    VehiclesPage --> VehicleForm
    VehiclesPage --> VehicleServices
    VehiclesPage --> VehicleList
    VehiclesPage --> Pagination
    BookingsPage --> MonthCalendar
    BookingsPage --> DaySlots
    BookingsPage --> UpcomingBookings
    App -. "api.ts" .-> API["Backend API"]
    LoginForm -. "api.ts" .-> API
    RegisterForm -. "api.ts" .-> API
    VehiclesPage -. "api.ts" .-> API
    VehicleServices -. "api.ts" .-> API
    Dashboard -. "api.ts" .-> API
    BookingsPage -. "api.ts" .-> API
    DaySlots -. "api.ts" .-> API
    UpcomingBookings -. "api.ts" .-> API
```

Dáta tečú zhora nadol cez props, udalosti idú hore cez funkcie v props (`onLogin`, `onSave`, `onDelete`, ...).
Prihláseného používateľa drží `App` (token je v httpOnly cookie, `App` sa pri štarte len opýta
`GET /auth/me`), autá a stránkovanie `VehiclesPage`,
zobrazený mesiac, otvorený deň a rezervácie `BookingsPage`.

## Stránky

| Adresa | Čo zobrazí |
|---|---|
| `/login` | prihlásenie |
| `/register` | registrácia nového účtu |
| `/` | úvodná stránka s menu |
| `/vehicles` | zoznam áut, len pre admina (ostatných presmeruje na `/`) |
| `/bookings` | kalendár s termínmi servisu |
| `/prices` | cenník |
| `/shop` | e-shop (pripravujeme) |
| hocičo iné | prihláseného presmeruje na `/`, neprihláseného na `/login` |

Prihlásený sa na `/login` a `/register` nedostane (presmeruje ho na `/`), neprihlásený vidí len tieto dve stránky.

Vozový park (karta v menu, odkaz v hlavičke aj stránka `/vehicles`) vidí len admin. Je to len
pohodlie pre používateľa, skutočnú kontrolu oprávnení robí backend (vodičovi vráti `403`).

Pastelové farby termínov sú v `index.css` zapísané cez `oklch()`: každá hodina má vlastný odtieň
(posiela ho `slots.ts` v premennej `--hue`), svetlosť a sýtosť majú všetky rovnakú.
