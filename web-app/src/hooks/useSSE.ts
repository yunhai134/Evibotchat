import { useCallback, useRef } from "react"
import { useChatStore } from "@/stores/chat"
import type { Source, QaOption } from "@/types/stream"

const API_BASE = ""

export function useSSE() {
  const abortRef = useRef<AbortController | null>(null)

  const addMessage = useChatStore((s) => s.addMessage)
  const appendToken = useChatStore((s) => s.appendToken)
  const setSources = useChatStore((s) => s.setSources)
  const setQaOptions = useChatStore((s) => s.setQaOptions)
  const setPhase = useChatStore((s) => s.setPhase)
  const finishStream = useChatStore((s) => s.finishStream)
  const setError = useChatStore((s) => s.setError)

  const send = useCallback(
    (question: string) => {
      if (abortRef.current) abortRef.current.abort()
      const controller = new AbortController()
      abortRef.current = controller

      // 用户消息
      addMessage({
        id: `user-${Date.now()}`,
        role: "user",
        content: question,
        isStreaming: false,
        phase: null,
        sources: [],
        qaOptions: [],
      })

      // 助手消息（流式）
      const msgId = `assistant-${Date.now()}`
      addMessage({
        id: msgId,
        role: "assistant",
        content: "",
        isStreaming: true,
        phase: "retrieving",
        sources: [],
        qaOptions: [],
      })

      fetch(`${API_BASE}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
        signal: controller.signal,
      })
        .then(async (res) => {
          if (!res.ok) throw new Error(`HTTP ${res.status}`)

          const reader = res.body?.getReader()
          if (!reader) throw new Error("no body reader")

          const decoder = new TextDecoder()
          let buffer = ""

          while (true) {
            const { done, value } = await reader.read()
            if (done) break

            buffer += decoder.decode(value, { stream: true })

            // 按 \n\n 分隔 SSE 事件块
            const blocks = buffer.split("\n\n")
            buffer = blocks.pop() ?? ""

            for (const block of blocks) {
              const trimmed = block.trim()
              if (!trimmed) continue

              // 解析 event 行
              const eventMatch = trimmed.match(/^event:\s*(\S+)/m)
              const eventType = eventMatch?.[1] ?? null

              // 解析 data 行（SSE 多行 data 规范：多个 data: 行用 \n 连接）
              const dataLines = trimmed
                .split("\n")
                .filter((l) => l.startsWith("data:"))
                .map((l) => l.replace(/^data:\s?/, ""))
              const dataText = dataLines.length > 0 ? dataLines.join("\n") : null

              if (!dataText) continue

              if (eventType === "sources") {
                try {
                  setSources(JSON.parse(dataText.trim()) as Source[])
                } catch { /* ignore parse errors */ }
              } else if (eventType === "qa_options") {
                try {
                  setQaOptions(JSON.parse(dataText.trim()) as QaOption[])
                } catch { /* ignore parse errors */ }
              } else if (eventType === "phase") {
                setPhase(dataText.trim() as "retrieving" | "thinking" | "generating")
              } else if (eventType === "done") {
                finishStream()
              } else if (!eventType && dataText.trim() !== "[DONE]") {
                // 纯文本 token（无 event 行），保留原始空白
                appendToken(dataText)
              } else if (dataText.trim() === "[DONE]") {
                finishStream()
              }
            }
          }

          // 流结束后再次 finish
          finishStream()
        })
        .catch((err) => {
          if (err.name !== "AbortError") {
            setError(err.message)
          }
        })
    },
    [addMessage, appendToken, setSources, setQaOptions, setPhase, finishStream, setError]
  )

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    finishStream()
  }, [finishStream])

  return { send, cancel }
}