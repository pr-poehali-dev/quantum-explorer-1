import { Suspense, useState } from "react"
import Spline from "@splinetool/react-spline"

export default function SplineScene() {
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)

  const handleLoad = () => {
    console.log("Spline scene loaded successfully")
    setIsLoading(false)
    setHasError(false)
  }

  const handleError = (error: unknown) => {
    console.log("Spline scene failed to load:", error)
    setIsLoading(false)
    setHasError(true)
  }

  return (
    <div className="absolute inset-0 w-full h-full bg-background">
      {isLoading && (
        <div className="absolute inset-0 w-full h-full flex items-center justify-center">
          <div className="text-foreground text-center">
            <div className="text-lg mb-2">Загрузка 3D сцены...</div>
            <div className="text-sm opacity-70">Пожалуйста, подождите</div>
          </div>
        </div>
      )}

      {hasError && (
        <div className="absolute inset-0 w-full h-full flex items-center justify-center">
          <div className="text-foreground text-center">
            <div className="text-lg mb-2">3D сцена недоступна</div>
            <div className="text-sm opacity-70">Не удалось загрузить 3D модель</div>
          </div>
        </div>
      )}

      {!hasError && (
        <Suspense fallback={null}>
          <Spline
            scene="https://prod.spline.design/l8gr6AhxxCqDIdBx/scene.splinecode"
            onLoad={handleLoad}
            onError={handleError}
            style={{
              width: "100%",
              height: "100%",
              background: "transparent",
            }}
          />
        </Suspense>
      )}
    </div>
  )
}
