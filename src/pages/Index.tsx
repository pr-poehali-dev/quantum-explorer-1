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
    buttonClass: "bg-[#9B59B6] hover:bg-[#A96BC8]",
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
          className="relative rounded-4xl py-7 mx-4 md:mx-0 w-[calc(100%-2rem)] md:w-full bg-card border border-solid border-border pb-20"
          style={{
            backgroundImage: `
              linear-gradient(var(--border) 1px, transparent 1px),
              linear-gradient(90deg, var(--border) 1px, transparent 1px)
            `,
            backgroundSize: "40px 40px",
          }}
        >
          <div className="absolute top-8 left-8 text-foreground opacity-50 text-5xl font-extralight font-sans leading-[0rem]">
            +
          </div>
          <div className="absolute top-8 right-8 text-foreground opacity-50 text-5xl font-sans leading-[0] font-extralight">
            +
          </div>
          <div className="absolute bottom-8 left-8 text-foreground opacity-50 text-5xl font-sans font-extralight">
            +
          </div>
          <div className="absolute bottom-8 right-8 text-foreground opacity-50 text-5xl font-sans font-extralight">
            +
          </div>

          <div className="px-6 md:px-16">
            <h2
              className="text-foreground text-3xl md:text-4xl font-bold mb-2 text-center"
              style={{ fontFamily: "var(--font-montserrat)" }}
            >
              Хиты продаж
            </h2>
            <p className="text-muted-foreground text-sm font-mono text-center mb-10">
              Самые популярные сладости нашего магазина
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {popularSweets.map((item) => (
                <div
                  key={item.name}
                  className="bg-background/50 border border-border rounded-2xl p-6 flex flex-col items-center text-center hover:border-primary/50 transition-all duration-300 hover:shadow-[0_0_30px_hsl(var(--primary)/0.1)]"
                >
                  <span className="text-6xl mb-4">{item.emoji}</span>
                  <h3 className="text-foreground font-mono font-bold text-lg mb-1">{item.name}</h3>
                  <p className="text-muted-foreground font-mono text-sm mb-4">{item.desc}</p>
                  <span className="text-primary font-mono font-bold text-xl mb-4">{item.price}</span>
                  <button className="bg-[#9B59B6] hover:bg-[#A96BC8] text-primary-foreground px-6 py-2 rounded-full font-mono text-sm font-semibold hover:scale-105 transition-all duration-300 flex items-center gap-2">
                    В корзину <Icon name="ShoppingCart" size={16} />
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