import { useChatStore } from "@/stores/chat"
import { motion } from "framer-motion"
import { AssistantAvatar } from "./AssistantAvatar"

function LLMBadge() {
  const llmStatus = useChatStore((s) => s.llmStatus)
  const llmModel = useChatStore((s) => s.llmModel)

  if (llmStatus === "loading") return null

  if (llmStatus === "connected") {
    return (
      <div className="mt-3 rounded-md border-l-3 border-emerald-400 bg-emerald-50/70 px-3.5 py-2 text-emerald-800 dark:bg-emerald-950/25 dark:text-emerald-300 text-xs">
        <strong>LLM 已连接</strong> —— 当前使用 <code className="text-[11px] bg-emerald-100/70 dark:bg-emerald-900/40 px-1 rounded">{llmModel ?? "外部模型"}</code>{" "}
        进行智能回答生成，回答会更准确、结构化。
      </div>
    )
  }

  return (
    <div className="mt-3 rounded-md border-l-3 border-primary bg-primary/5 px-3.5 py-2 text-primary/90 dark:text-primary/80 text-xs">
      <strong>本地模式</strong> —— 系统将直接展示知识库检索到的相关资料片段，供您参考。
    </div>
  )
}

export function WelcomeMessage() {
  const llmStatus = useChatStore((s) => s.llmStatus)

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="flex items-start gap-3"
    >
      <AssistantAvatar size={32} />
      <div className="rounded-xl bg-card border border-border/50 shadow-sm p-4 text-sm font-medium leading-relaxed max-w-[80%] md:max-w-[75%]">
        <p className="font-bold text-foreground mb-1">
          你好！我是 <strong>Evibot（循证）</strong>，您的家庭医学知识助手。
        </p>
        <p className="text-foreground mt-2">
          我可以基于本地医学教材知识库，为您解答各类医学健康问题。
        </p>
        <LLMBadge />
        <div className="mt-3 rounded-md border-l-3 border-amber-400 bg-amber-50/60 px-3.5 py-2 text-amber-800 dark:bg-amber-950/20 dark:text-amber-300 text-xs">
          <strong>温馨提示</strong>：我的回答仅供参考，不能替代专业医生的诊断和治疗建议。如有身体不适或紧急症状，请及时就医。
        </div>
        {llmStatus !== "loading" && (
          <p className="text-foreground mt-3 text-xs font-medium">
            {llmStatus === "connected"
              ? "您可以在下方输入框中输入医学问题，例如：「甲状腺功能减退的症状有哪些？」"
              : "您可以在下方输入框中输入医学问题，系统将从医学知识库中检索相关片段。例如：「感冒该吃什么药？」"}
          </p>
        )}
      </div>
    </motion.div>
  )
}
