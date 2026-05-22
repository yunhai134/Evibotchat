import { useEffect } from "react"
import { useChatStore } from "@/stores/chat"

const API_BASE = ""

export function useLLMStatus() {
  const setLLMStatus = useChatStore((s) => s.setLLMStatus)

  useEffect(() => {
    let cancelled = false

    async function fetchStatus() {
      try {
        const res = await fetch(`${API_BASE}/health`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        if (cancelled) return

        if (data.llm_connected) {
          setLLMStatus("connected", data.chat_model ?? undefined)
        } else {
          setLLMStatus("disconnected", null)
        }
      } catch {
        if (!cancelled) {
          setLLMStatus("disconnected", null)
        }
      }
    }

    fetchStatus()
    return () => { cancelled = true }
  }, [setLLMStatus])
}