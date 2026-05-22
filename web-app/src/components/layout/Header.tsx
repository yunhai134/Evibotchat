import { useChatStore } from "@/stores/chat"
import type { LLMStatus } from "@/stores/chat"
import { useTheme } from "@/hooks/useTheme"
import { Button } from "@/components/ui/button"
import { useLLMStatus } from "@/hooks/useLLMStatus"
import { useState } from "react"
import { AboutModal } from "@/components/chat/AboutModal"

function StatusDot({ status }: { status: LLMStatus }) {
  const base = "mr-1 inline-block h-1.5 w-1.5 rounded-full"
  if (status === "loading") {
    return <span className={`${base} bg-muted-foreground animate-pulse`} />
  }
  if (status === "connected") {
    return <span className={`${base} bg-emerald-500`} />
  }
  return <span className={`${base} bg-primary`} />
}

function StatusLabel({ status, model }: { status: LLMStatus; model: string | null }) {
  if (status === "loading") {
    return <span>检测中</span>
  }
  if (status === "connected") {
    return <span className="flex items-center gap-1">{model ?? "LLM"} <span className="text-[10px] opacity-60">在线</span></span>
  }
  return <span>本地模式</span>
}

export function Header() {
  useLLMStatus()
  const isStreaming = useChatStore((s) => s.isStreaming)
  const clearError = useChatStore((s) => s.clearError)
  const clearMessages = useChatStore((s) => s.clearMessages)
  const llmStatus = useChatStore((s) => s.llmStatus)
  const llmModel = useChatStore((s) => s.llmModel)
  const { isDark, toggleTheme } = useTheme()
  const [aboutOpen, setAboutOpen] = useState(false)

  const statusColor =
    llmStatus === "loading"
      ? "bg-muted text-muted-foreground"
      : llmStatus === "connected"
        ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400"
        : "bg-primary/8 text-primary dark:bg-primary/15"

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/80 backdrop-blur-xl">
      <div className="flex h-12 items-center justify-between px-4 md:px-6">
        <div className="flex items-center gap-2">
          <svg
            viewBox="0 0 24 24"
            className="h-5 w-5 text-primary"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
          </svg>
          <span className="font-bold text-base">Evibot</span>
          <span className="hidden sm:inline text-sm font-medium text-foreground">
            循证医学助手
          </span>

          {/* Status badges */}
          <span
            className={`ml-2 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${
              isStreaming
                ? "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400"
                : "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400"
            }`}
          >
            <span
              className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${
                isStreaming ? "bg-amber-500 animate-pulse" : "bg-emerald-500"
              }`}
            />
            {isStreaming ? "思考中" : "就绪"}
          </span>

          <span className={`ml-1 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${statusColor}`}>
            <StatusDot status={llmStatus} />
            <StatusLabel status={llmStatus} model={llmModel} />
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-9 gap-1.5 rounded-lg px-3 text-sm font-semibold text-foreground hover:text-foreground hover:bg-primary/8"
            onClick={() => setAboutOpen(true)}
          >
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4M12 8h.01" />
            </svg>
            <span className="hidden sm:inline">关于</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-9 gap-1.5 rounded-lg px-3 text-sm font-semibold text-foreground hover:text-foreground hover:bg-primary/8"
            onClick={toggleTheme}
            title={isDark ? "切换亮色模式" : "切换暗色模式"}
          >
            {isDark ? (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
            <span className="hidden sm:inline">{isDark ? "亮色" : "暗色"}</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-9 gap-1.5 rounded-lg px-3 text-sm font-semibold text-foreground hover:text-foreground hover:bg-destructive/8"
            onClick={() => { clearMessages(); clearError() }}
            title="清空对话"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            <span className="hidden sm:inline">清空</span>
          </Button>
        </div>
      </div>

      <AboutModal open={aboutOpen} onClose={() => setAboutOpen(false)} />
    </header>
  )
}
