import { useState, useRef, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { useChatStore } from "@/stores/chat"
import { useSSE } from "@/hooks/useSSE"
import { motion } from "framer-motion"

export function ChatInput() {
  const [input, setInput] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const isStreaming = useChatStore((s) => s.isStreaming)
  const error = useChatStore((s) => s.error)
  const clearError = useChatStore((s) => s.clearError)
  const { send } = useSSE()

  const handleSend = useCallback(() => {
    const text = input.trim()
    if (!text || isStreaming) return

    setInput("")
    clearError()
    send(text)
  }, [input, isStreaming, clearError, send])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.15 }}
      className="border-t border-border/40 bg-background/80 backdrop-blur-xl px-4 py-3 pb-safe md:px-6"
    >
      <div className="mx-auto max-w-3xl">
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-2.5 rounded-lg bg-destructive/8 border border-destructive/15 px-3.5 py-2 text-xs font-medium text-destructive"
          >
            {error}
          </motion.div>
        )}

        <div className="relative flex items-end gap-2 rounded-xl border border-border/60 bg-card p-1.5 shadow-sm focus-within:ring-1.5 focus-within:ring-primary/25 focus-within:border-primary/25 transition-all duration-200">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入医学问题，如：感冒该吃什么药？"
            rows={1}
            className="flex-1 resize-none bg-transparent px-3 py-2 text-sm font-medium outline-none placeholder:text-muted-foreground/50"
            disabled={isStreaming}
          />

          <Button
            size="icon"
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className="shrink-0 rounded-lg bg-primary text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors duration-150 disabled:opacity-40"
          >
            {isStreaming ? (
              <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            ) : (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            )}
          </Button>
        </div>

        <p className="mt-1.5 text-center text-[10px] font-semibold text-foreground/60 tracking-wide">
          Enter 发送 · Shift+Enter 换行
        </p>
      </div>
    </motion.div>
  )
}
