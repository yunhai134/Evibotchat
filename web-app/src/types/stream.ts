export type StreamPhase = "retrieving" | "thinking" | "generating" | null

export interface Source {
  source: string
  page: string | number
  relevance: string
}

export interface QaOption {
  question: string
  answer: string
  disease: string
  score: number
  _expanded?: boolean
}

export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  isStreaming: boolean
  phase: StreamPhase
  sources: Source[]
  qaOptions: QaOption[]
}

export type SSEEvent =
  | { type: "message"; data: string }
  | { type: "sources"; data: Source[] }
  | { type: "qa_options"; data: QaOption[] }
  | { type: "phase"; data: StreamPhase }
  | { type: "done" }
  | { type: "error"; data: string }