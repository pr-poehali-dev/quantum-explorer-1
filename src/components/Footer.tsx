import Icon from "@/components/ui/icon"

export default function Footer() {
  return (
    <footer className="w-full px-6 relative py-0 mt-28 h-auto mb-0 bg-card overflow-hidden">
      <div className="absolute top-6 right-10 text-primary text-3xl animate-bounce">✨</div>
      <div className="absolute top-20 right-40 text-pink-400 text-2xl animate-pulse">💖</div>
      <div className="absolute bottom-32 right-16 text-primary text-xl animate-bounce delay-300">⭐</div>
      <div className="absolute top-12 left-[60%] text-pink-300 text-lg animate-pulse">💅</div>
      <div className="absolute bottom-20 right-48 text-primary text-2xl animate-bounce">🎀</div>

      <div className="max-w-[1200px] mx-auto">
        <div className="flex flex-col md:flex-row items-center justify-between">
          <div className="flex-1 max-w-lg mt-8">
            <h2
              className="text-foreground text-4xl md:text-5xl mb-4 leading-[3.5rem] md:leading-[4rem] font-semibold text-center md:text-left mt-0"
              style={{ fontFamily: "var(--font-barbie)" }}
            >
              <span className="text-primary">Сладости</span> для
              <br />
              каждого вайба 💕
            </h2>

            <div className="space-y-4 text-foreground">
              <div className="flex items-start gap-3">
                <span className="text-primary mt-1 text-lg">💗</span>
                <p className="text-sm">Ваще без шуток — наши десерты делают жизнь ярче. Каждый создан с любовью и из натуральных ингредиентов, no cap 💯</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="text-primary mt-1 text-lg">🦄</span>
                <p className="text-sm">Доставим радость по всей России — от подарочных боксов до любимых конфеток на каждый день. Slay! ✨</p>
              </div>
            </div>
          </div>

          <div className="hidden md:flex flex-1 justify-end items-center relative">
            <div className="relative flex items-center justify-center">
              <div className="absolute -inset-8 bg-primary/10 rounded-full blur-3xl animate-pulse"></div>
              <span className="text-[120px] relative z-10 drop-shadow-[0_0_30px_hsl(330,100%,50%,0.3)]">🧁</span>
            </div>
          </div>
        </div>

        <div className="md:hidden flex justify-center mt-12">
          <span className="text-[100px] drop-shadow-[0_0_20px_hsl(330,100%,50%,0.3)]">🧁</span>
        </div>

        <div id="contact" className="w-full px-6 py-16 flex flex-col md:flex-row items-center justify-center md:justify-between gap-6 md:gap-0 border-t border-border mt-16">
          <div className="flex flex-col md:flex-row gap-2 text-center md:text-left">
            <h2 className="text-foreground text-xl font-bold" style={{ fontFamily: "var(--font-barbie)" }}>Есть вопросики?</h2>
            <p className="text-foreground font-mono font-normal text-base">Пиши нам — поможем с выбором! 💌</p>
          </div>

          <a href="mailto:hello@example.com">
            <button className="bg-primary text-primary-foreground px-8 py-4 rounded-full font-semibold text-lg whitespace-nowrap hover:scale-110 hover:shadow-[0_0_30px_hsl(330,100%,50%,0.5)] transition-all duration-300 font-mono flex items-center gap-2 hover:rotate-1">
              Написать нам 💌
              <Icon name="ArrowUpRight" size={20} />
            </button>
          </a>
        </div>

        <div className="w-full px-6 py-4 border-t border-border flex md:flex-row items-center justify-between gap-2 flex-row">
          <p className="text-muted-foreground text-sm font-mono">2025 SweetShop 💖</p>
          <p className="text-muted-foreground text-sm font-mono">poehali.dev</p>
        </div>
      </div>
    </footer>
  )
}
