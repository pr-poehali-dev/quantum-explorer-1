import SplineScene from "@/components/SplineScene"
import Header from "@/components/Header"
import RotatingTextAccent from "@/components/RotatingTextAccent"
import Footer from "@/components/Footer"
import HeroTextOverlay from "@/components/HeroTextOverlay"

const CDN_BASE = "https://cdn.poehali.dev/templates/meet-jack"

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

          <div className="px-6 md:px-40">
            <div className="flex items-center justify-center mb-3.5 md:gap-11">
              <div className="flex flex-col items-center">
                <img src={`${CDN_BASE}/jack-front.png`} alt="Макс спереди" className="w-48 h-48 md:w-56 md:h-56 object-contain" />
              </div>

              <div className="flex flex-col items-center">
                <img src={`${CDN_BASE}/jack-side.png`} alt="Макс сбоку" className="w-48 h-48 md:w-56 md:h-56 object-contain" />
              </div>

              <div className="flex flex-col items-center">
                <img src={`${CDN_BASE}/jack-back.png`} alt="Макс сзади" className="w-48 h-48 md:w-56 md:h-56 object-contain" />
              </div>
            </div>

            <div className="flex flex-col gap-2 max-w-5xl">
              <div className="flex items-center gap-4">
                <span className="text-accent font-mono text-sm">Имя</span>
                <span className="text-foreground font-mono text-sm">Макс</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-accent font-mono text-sm">Вид</span>
                <span className="text-foreground font-mono text-sm">Инопланетянин с планеты Флэпджек</span>
              </div>
              <div className="flex items-start gap-4">
                <span className="text-accent font-mono text-sm">Характер</span>
                <span className="text-foreground font-mono text-sm">
                  Любопытный, гибкий, немного расслабленный - но острый, когда дело касается баз данных и организации информации.
                </span>
              </div>
            </div>
          </div>
        </section>
      </div>
      <Footer />
    </div>
  )
}

export default Index
