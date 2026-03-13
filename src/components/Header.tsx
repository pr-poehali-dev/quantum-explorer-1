import { Button } from "@/components/ui/button"
import Icon from "@/components/ui/icon"

export default function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/0 backdrop-blur-sm">
      <div className="flex items-center justify-between px-6 py-4 text-transparent">
        <div className="flex items-center gap-3">
          <span
            className="text-foreground text-xl font-bold"
            style={{ fontFamily: "var(--font-barbie)" }}
          >
            💖 SweetShop
          </span>
        </div>

        <div className="flex items-center gap-2">
          <a href="#catalog">
            <Button
              className="bg-primary text-primary-foreground rounded-full px-6 transition-all duration-300 hover:scale-110 hover:shadow-[0_0_25px_hsl(330,100%,50%,0.5)] hover:rotate-1"
              style={{ paddingLeft: "24px", paddingRight: "16px" }}
            >
              Каталог 🛍️ <Icon name="ArrowUpRight" size={16} />
            </Button>
          </a>
        </div>
      </div>
    </header>
  )
}
