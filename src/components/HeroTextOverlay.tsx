export default function HeroTextOverlay() {
  return (
    <div className="absolute top-30 md:top-48 left-8 z-10">
      <h1
        className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-wider mb-3.5 opacity-100"
        style={{
          fontFamily: "var(--font-barbie)",
          color: "hsl(330, 100%, 50%)",
          WebkitTextStroke: "2px hsl(330, 60%, 80%)",
          paintOrder: "stroke fill",
          textShadow: "0 0 40px hsl(330, 100%, 50%, 0.4)",
        }}
      >
        Sweeties
      </h1>
      <p
        className="text-foreground text-sm md:text-base max-w-xs tracking-widest lg:text-base"
        style={{ fontFamily: "var(--font-montserrat)" }}
      >
        Онлайн-магазин
        <br />
        вкусных подарков 💕
      </p>
    </div>
  )
}
