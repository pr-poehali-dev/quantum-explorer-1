import SplineScene from "@/components/SplineScene"
import Header from "@/components/Header"
import RotatingTextAccent from "@/components/RotatingTextAccent"
import Footer from "@/components/Footer"
import HeroTextOverlay from "@/components/HeroTextOverlay"
import Icon from "@/components/ui/icon"

const popularSweets = [
  {
    name: "Бельгийский шоколад",
    desc: "Ручная работа, натуральное какао",
    price: "890 ₽",
    emoji: "🍫",
  },
  {
    name: "Макаруны ассорти",
    desc: "12 штук, 6 вкусов",
    price: "1 290 ₽",
    emoji: "🧁",
  },
  {
    name: "Подарочный набор",
    desc: "Конфеты, мармелад, пастила",
    price: "2 490 ₽",
    emoji: "🎁",
  },
  {
    name: "Медовая пастила",
    desc: "Яблочная, с облепихой и вишней",
    price: "590 ₽",
    emoji: "🍯",
  },
  {
    name: "Трюфели ручной работы",
    desc: "9 штук, тёмный и молочный шоколад",
    price: "1 490 ₽",
    emoji: "🍬",
  },
  {
    name: "Фруктовый мармелад",
    desc: "Без сахара, на натуральном соке",
    price: "690 ₽",
    emoji: "🍊",
  },
]

const Index = () => {
  return (
    <div className="w-full min-h-screen py-0 bg-background">
      <div className="max-w-[1200px] mx-auto">
        <main className="w-full relative h-[600px]">
          <Header />
          <SplineScene />
          <HeroTextOverlay />
          <RotatingTextAccent />
        </main>

        <section
          id="catalog"
          className="relative rounded-4xl py-7 mx-4 md:mx-0 w-[calc(100%-2rem)] md:w-full bg-card border border-solid border-border pb-20 overflow-hidden"
        >
          <div className="absolute top-6 left-6 text-primary/40 text-3xl animate-pulse">💖</div>
          <div className="absolute top-6 right-6 text-primary/40 text-3xl animate-bounce">✨</div>
          <div className="absolute bottom-6 left-6 text-primary/40 text-3xl animate-bounce">🎀</div>
          <div className="absolute bottom-6 right-6 text-primary/40 text-3xl animate-pulse">💅</div>

          <div className="px-6 md:px-16">
            <h2
              className="text-foreground text-3xl md:text-5xl mb-2 text-center"
              style={{ fontFamily: "var(--font-barbie)" }}
            >
              Хиты продаж 🔥
            </h2>
            <p className="text-muted-foreground text-sm text-center mb-10" style={{ fontFamily: "var(--font-montserrat)" }}>
              Самые популярные сладости — разбирают мгновенно, no cap 💯
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {popularSweets.map((item) => (
                <div
                  key={item.name}
                  className="bg-background/60 border border-border rounded-3xl p-6 flex flex-col items-center text-center hover:border-primary/50 transition-all duration-300 hover:shadow-[0_0_30px_hsl(330,100%,50%,0.15)] hover:scale-[1.02] hover:-rotate-1"
                >
                  <span className="text-6xl mb-4 drop-shadow-[0_0_15px_hsl(330,100%,50%,0.2)]">{item.emoji}</span>
                  <h3 className="text-foreground font-bold text-lg mb-1" style={{ fontFamily: "var(--font-montserrat)" }}>{item.name}</h3>
                  <p className="text-muted-foreground text-sm mb-4" style={{ fontFamily: "var(--font-montserrat)" }}>{item.desc}</p>
                  <span className="text-primary font-bold text-xl mb-4" style={{ fontFamily: "var(--font-montserrat)" }}>{item.price}</span>
                  <button className="bg-primary text-primary-foreground px-6 py-2 rounded-full text-sm font-semibold hover:scale-110 transition-all duration-300 flex items-center gap-2 hover:shadow-[0_0_20px_hsl(330,100%,50%,0.4)] hover:rotate-1" style={{ fontFamily: "var(--font-montserrat)" }}>
                    В корзину 🛒
                  </button>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
      <Footer />
    </div>
  )
}

export default Index
