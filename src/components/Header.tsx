import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import Icon from "@/components/ui/icon"
import { useAuth } from "@/context/AuthContext"
import { useCart } from "@/context/CartContext"

export default function Header() {
  const { user } = useAuth()
  const { totalCount } = useCart()

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/0 backdrop-blur-sm">
      <div className="flex items-center justify-between px-6 py-4 text-transparent">
        <div className="flex items-center gap-3">
          <Link to="/" className="text-foreground text-xl font-bold" style={{ fontFamily: "var(--font-montserrat)" }}>
            🍬 SweetShop
          </Link>
        </div>

        <div className="flex items-center gap-2">
          <a href="#catalog">
            <Button
              className="bg-primary text-primary-foreground rounded-full px-6 transition-all duration-300 hover:scale-105 hover:shadow-[0_0_20px_hsl(var(--primary)/0.5)]"
              style={{ paddingLeft: "24px", paddingRight: "16px" }}
            >
              Каталог <Icon name="ArrowUpRight" size={16} />
            </Button>
          </a>

          <Link to="/cart">
            <Button variant="outline" size="icon" className="rounded-full relative">
              <Icon name="ShoppingCart" size={18} />
              {totalCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-primary text-primary-foreground text-xs rounded-full w-5 h-5 flex items-center justify-center font-mono font-bold">
                  {totalCount}
                </span>
              )}
            </Button>
          </Link>

          {user ? (
            <Link to="/profile">
              <Button variant="outline" size="icon" className="rounded-full">
                <Icon name="User" size={18} />
              </Button>
            </Link>
          ) : (
            <Link to="/login">
              <Button variant="outline" className="rounded-full font-mono text-sm">
                Войти
              </Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
