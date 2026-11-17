import { Link } from 'react-router'
import cartOutline from '../assets/cart-outline.svg'

// E-shop zatiaľ neexistuje, stránka len oznamuje, že sa pripravuje.
function ShopPage() {
  return (
    <section className="coming-soon">
      {/* Import obrázka z assets: Vite z neho spraví adresu súboru. alt="" znamená, že obrázok
          je len ozdoba a čítačka obrazovky ho má preskočiť. */}
      <img src={cartOutline} alt="" width={160} height={144} />
      <h2>E-shop pripravujeme</h2>
      <p>Čoskoro tu nájdeš náhradné diely, oleje a autokozmetiku. Dovtedy si môžeš rezervovať termín servisu.</p>
      <Link className="button-link" to="/bookings">
        Rezervovať termín
      </Link>
    </section>
  )
}

export default ShopPage
