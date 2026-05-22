import { motion } from "framer-motion"
import { useChatStore } from "@/stores/chat"
import { QaOptionsMenu } from "./SuggestionCard"
import { MarkdownContent } from "./MarkdownContent"
import { AssistantAvatar } from "./AssistantAvatar"
import type { StreamPhase } from "@/types/stream"

const PHASE_LABELS: Record<NonNullable<StreamPhase>, string> = {
  retrieving: "解析中",
  thinking: "思考中",
  generating: "输出中",
}

interface Props {
  index: number
}

export function ChatMessage({ index }: Props) {
  const message = useChatStore((s) => s.messages[index])
  if (!message) return null
  const isUser = message.role === "user"
  const showPhase = !isUser && message.isStreaming && message.phase && !message.content

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.35,
        ease: [0.25, 0.46, 0.45, 0.94],
        delay: 0.03,
      }}
      className={`flex items-start gap-3 ${isUser ? "flex-row-reverse" : ""}`}
    >
      {/* Avatar */}
      {isUser ? (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 260, damping: 20, delay: 0.08 }}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold shadow-md bg-primary text-primary-foreground"
        >
          U
        </motion.div>
      ) : (
        <AssistantAvatar size={32} streaming={message.isStreaming} />
      )}

      <div className={`max-w-[80%] md:max-w-[75%] ${isUser ? "text-right" : ""}`}>
        {/* Message bubble */}
        <div
          className={`relative inline-block rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? "bg-primary text-primary-foreground rounded-tr-sm shadow-sm"
              : "bg-card border border-border/60 shadow-sm rounded-tl-sm dark:border-border/40"
          }`}
        >
          {showPhase ? (
            <div className="flex items-center gap-2 text-foreground">
              <div className="flex gap-1">
                <motion.span
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1.2, repeat: Infinity, delay: 0 }}
                  className="h-1.5 w-1.5 rounded-full bg-primary"
                />
                <motion.span
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1.2, repeat: Infinity, delay: 0.2 }}
                  className="h-1.5 w-1.5 rounded-full bg-primary"
                />
                <motion.span
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1.2, repeat: Infinity, delay: 0.4 }}
                  className="h-1.5 w-1.5 rounded-full bg-primary"
                />
              </div>
              <span className="text-xs font-semibold">{PHASE_LABELS[message.phase!]}</span>
            </div>
          ) : (
            <>
              <MarkdownContent content={message.content} />

              {message.isStreaming && (
                <span className="inline-flex ml-1 gap-1">
                  <motion.span
                    animate={{ y: [0, -3, 0] }}
                    transition={{ duration: 0.5, repeat: Infinity, delay: 0 }}
                    className="h-1 w-1 rounded-full bg-current opacity-50"
                  />
                  <motion.span
                    animate={{ y: [0, -3, 0] }}
                    transition={{ duration: 0.5, repeat: Infinity, delay: 0.12 }}
                    className="h-1 w-1 rounded-full bg-current opacity-50"
                  />
                  <motion.span
                    animate={{ y: [0, -3, 0] }}
                    transition={{ duration: 0.5, repeat: Infinity, delay: 0.24 }}
                    className="h-1 w-1 rounded-full bg-current opacity-50"
                  />
                </span>
              )}
            </>
          )}
        </div>

        {/* QA Options */}
        {!isUser && !message.isStreaming && message.qaOptions && message.qaOptions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.15 }}
            className="mt-2"
          >
            <QaOptionsMenu options={message.qaOptions} messageId={message.id} />
          </motion.div>
        )}

        {/* Source tags */}
        {!isUser && !message.isStreaming && message.sources && message.sources.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.25 }}
            className="mt-1.5 flex flex-wrap gap-1.5"
          >
            {message.sources.map((src, i) => (
              <motion.span
                key={i}
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.25 + i * 0.04 }}
                className="inline-flex items-center rounded-full bg-muted/70 px-2 py-0.5 text-[10px] font-semibold text-foreground border border-border/40"
              >
                {src.source} · 第{src.page}页
              </motion.span>
            ))}
          </motion.div>
        )}
      </div>
    </motion.div>
  )
}
