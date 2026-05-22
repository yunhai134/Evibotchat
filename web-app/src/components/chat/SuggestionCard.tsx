import { motion, AnimatePresence } from "framer-motion"
import type { QaOption } from "@/types/stream"
import { useChatStore } from "@/stores/chat"

interface Props {
  options: QaOption[]
  messageId: string
}

export function QaOptionsMenu({ options, messageId }: Props) {
  const toggleQaOption = useChatStore((s) => s.toggleQaOption)
  const messages = useChatStore((s) => s.messages)
  const assistantMsg = messages.find((m) => m.id === messageId)
  const qaOptions = assistantMsg?.qaOptions ?? options

  if (!qaOptions || qaOptions.length === 0) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="mt-3 rounded-xl border bg-gradient-to-b from-card/95 to-muted/30 backdrop-blur-md shadow-lg shadow-black/5 dark:shadow-white/5 overflow-hidden"
    >
      {/* Header with accent line */}
      <div className="relative px-4 py-2.5 text-xs font-semibold text-muted-foreground border-b border-border/50 bg-muted/30">
        <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-amber-400 to-orange-400" />
        <span className="ml-2">相似问题</span>
      </div>

      <div className="divide-y divide-border/30">
        {qaOptions.map((opt, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.05, duration: 0.25 }}
          >
            <button
              type="button"
              onClick={() => toggleQaOption(messageId, idx)}
              className="group w-full flex items-start gap-3 px-4 py-3 text-left text-sm hover:bg-accent/40 transition-all duration-200"
            >
              {/* Animated chevron */}
              <motion.span
                animate={{ rotate: opt._expanded ? 90 : 0 }}
                transition={{ duration: 0.2, ease: "easeInOut" }}
                className="mt-0.5 shrink-0 text-muted-foreground group-hover:text-primary transition-colors"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path d="M9 5l7 7-7 7" />
                </svg>
              </motion.span>

              <div className="flex-1 min-w-0">
                <span className="text-foreground group-hover:text-primary transition-colors line-clamp-2">
                  {opt.question}
                </span>
                {opt.disease && (
                  <motion.span
                    whileHover={{ scale: 1.05 }}
                    className="mt-1 inline-flex rounded-full bg-primary/10 px-2.5 py-0.5 text-[10px] font-medium text-primary border border-primary/20"
                  >
                    {opt.disease}
                  </motion.span>
                )}
              </div>
            </button>

            <AnimatePresence>
              {opt._expanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
                  className="overflow-hidden"
                >
                  <div className="relative px-4 pb-4 pl-11 text-sm font-medium text-foreground leading-relaxed border-t border-dashed border-border/30 pt-3 bg-gradient-to-b from-muted/20 to-transparent">
                    {/* Left accent bar */}
                    <div className="absolute left-4 top-3 bottom-3 w-0.5 rounded-full bg-gradient-to-b from-primary/50 to-primary/20" />
                    {opt.answer.split("\n").map((line, i) => (
                      <p
                        key={i}
                        className={
                          line.startsWith("**") && line.endsWith("**")
                            ? "font-bold text-foreground mt-2.5 first:mt-0"
                            : "font-medium text-foreground mt-1.5 first:mt-0"
                        }
                      >
                        {line.replace(/\*\*/g, "")}
                      </p>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}