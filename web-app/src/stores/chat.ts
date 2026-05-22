import { create } from "zustand"
import type { ChatMessage, Source, QaOption, StreamPhase } from "@/types/stream"

export type LLMStatus = "loading" | "connected" | "disconnected"

interface ChatStore {
  messages: ChatMessage[]
  isStreaming: boolean
  error: string | null
  llmStatus: LLMStatus
  llmModel: string | null
  setLLMStatus: (status: LLMStatus, model?: string | null) => void
  addMessage: (msg: ChatMessage) => void
  updateLastMessage: (updates: Partial<ChatMessage>) => void
  appendToken: (token: string) => void
  setSources: (sources: Source[]) => void
  setQaOptions: (options: QaOption[]) => void
  setPhase: (phase: StreamPhase) => void
  toggleQaOption: (messageId: string, optionIndex: number) => void
  finishStream: () => void
  setError: (err: string) => void
  clearError: () => void
  clearMessages: () => void
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isStreaming: false,
  error: null,
  llmStatus: "loading",
  llmModel: null,

  setLLMStatus: (status, model) => set({ llmStatus: status, llmModel: model ?? null }),

  addMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, msg] })),

  updateLastMessage: (updates) =>
    set((s) => {
      const msgs = [...s.messages]
      const last = msgs[msgs.length - 1]
      if (last) {
        msgs[msgs.length - 1] = { ...last, ...updates }
      }
      return { messages: msgs }
    }),

  appendToken: (token) =>
    set((s) => {
      const msgs = [...s.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === "assistant") {
        msgs[msgs.length - 1] = { ...last, content: last.content + token }
      }
      return { messages: msgs }
    }),

  setSources: (sources) =>
    set((s) => {
      const msgs = [...s.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === "assistant") {
        msgs[msgs.length - 1] = { ...last, sources }
      }
      return { messages: msgs }
    }),

  setQaOptions: (options) =>
    set((s) => {
      const msgs = [...s.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === "assistant") {
        msgs[msgs.length - 1] = {
          ...last,
          qaOptions: options.map((o) => ({ ...o, _expanded: false })),
        }
      }
      return { messages: msgs }
    }),

  setPhase: (phase) =>
    set((s) => {
      const msgs = [...s.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === "assistant") {
        msgs[msgs.length - 1] = { ...last, phase }
      }
      return { messages: msgs }
    }),

  toggleQaOption: (messageId, optionIndex) =>
    set((s) => {
      const msgs = [...s.messages]
      const targetIdx = msgs.findIndex((m) => m.id === messageId)
      if (targetIdx === -1) return s
      const target = msgs[targetIdx]
      const updated = target.qaOptions.map((opt, i) =>
        i === optionIndex ? { ...opt, _expanded: !opt._expanded } : opt
      )
      msgs[targetIdx] = { ...target, qaOptions: updated }
      return { messages: msgs }
    }),

  finishStream: () =>
    set((s) => {
      const msgs = [...s.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === "assistant") {
        msgs[msgs.length - 1] = { ...last, isStreaming: false, phase: null }
      }
      return { messages: msgs, isStreaming: false }
    }),

  setError: (err) => set({ error: err, isStreaming: false }),

  clearError: () => set({ error: null }),

  clearMessages: () => set({ messages: [], error: null }),
}))