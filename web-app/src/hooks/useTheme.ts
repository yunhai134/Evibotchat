import { useCallback, useEffect, useState } from "react"

export function useTheme() {
  const [isDark, setIsDark] = useState(() => {
    if (typeof window === "undefined") return false
    return window.matchMedia("(prefers-color-scheme: dark)").matches
  })

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)")
    const handler = (e: MediaQueryListEvent) => {
      setIsDark(e.matches)
      document.documentElement.classList.toggle("dark", e.matches)
    }
    mq.addEventListener("change", handler)
    document.documentElement.classList.toggle("dark", isDark)
    return () => mq.removeEventListener("change", handler)
  }, [isDark])

  const toggleTheme = useCallback(() => {
    setIsDark((prev) => {
      const next = !prev
      document.documentElement.classList.toggle("dark", next)
      return next
    })
  }, [])

  return { isDark, toggleTheme }
}