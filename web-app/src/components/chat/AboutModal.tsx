import { motion, AnimatePresence } from "framer-motion"
import { useEffect, useRef } from "react"

interface Props {
  open: boolean
  onClose: () => void
}

export function AboutModal({ open, onClose }: Props) {
  const panelRef = useRef<HTMLDivElement>(null)

  // ESC 关闭
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [open, onClose])

  // 点击面板外部关闭
  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose()
      }
    }
    // 延迟绑定，避免打开按钮的 click 事件立即触发关闭
    const timer = setTimeout(() => {
      document.addEventListener("mousedown", handler)
    }, 0)
    return () => {
      clearTimeout(timer)
      document.removeEventListener("mousedown", handler)
    }
  }, [open, onClose])

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* 半透明遮罩 - 移动端更明显 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-[99] bg-black/20 backdrop-blur-[2px] sm:bg-black/10"
            onClick={onClose}
          />

          {/* 面板 */}
          <motion.div
            ref={panelRef}
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.97 }}
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
            className="fixed right-3 top-14 z-[100] mx-4 max-h-[80vh] w-[calc(100%-24px)] max-w-md overflow-y-auto rounded-xl border border-border/50 bg-card shadow-2xl sm:right-4"
          >
            {/* Header */}
            <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border/50 bg-card px-5 py-3">
              <div className="flex items-center gap-2.5">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10">
                  <svg
                    viewBox="0 0 24 24"
                    className="h-3.5 w-3.5 text-primary"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <circle cx="12" cy="12" r="10" />
                    <path d="M12 16v-4M12 8h.01" />
                  </svg>
                </div>
                <h2 className="text-sm font-semibold text-foreground">关于 Evibot</h2>
              </div>
              <button
                onClick={onClose}
                className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
                title="关闭"
              >
                <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Body */}
            <div className="px-5 py-4 space-y-4 text-sm text-muted-foreground">
              {/* 简介 */}
              <section>
                <h3 className="font-medium text-foreground mb-1.5">项目简介</h3>
                <p className="leading-relaxed text-xs">
                  Evibot 是一个个人学习性质的医学问答小项目，不带有商业目的。项目尝试用 RAG 技术把本地医学资料和检索增强生成结合起来，回答用户提出的医学问题。
                </p>
              </section>

              {/* 技术栈 */}
              <section>
                <h3 className="font-medium text-foreground mb-1.5">技术栈</h3>
                <div className="grid grid-cols-2 gap-3 text-[11px]">
                  <div>
                    <p className="font-medium text-foreground mb-1">前端</p>
                    <p className="space-y-0.5 leading-relaxed">
                      React 19 · Vite<br />
                      TypeScript · Tailwind CSS v4<br />
                      shadcn/ui · framer-motion<br />
                      Zustand · react-markdown
                    </p>
                  </div>
                  <div>
                    <p className="font-medium text-foreground mb-1">后端</p>
                    <p className="space-y-0.5 leading-relaxed">
                      FastAPI · Python 3.12<br />
                      LangChain · ChromaDB<br />
                      BGE-M3（向量模型）<br />
                      BGE-Reranker-v2-M3
                    </p>
                  </div>
                </div>
              </section>

              {/* 数据来源 */}
              <section>
                <h3 className="font-medium text-foreground mb-1.5">数据来源</h3>
                <div className="space-y-2">
                  <div className="rounded-lg border border-border/50 bg-muted/30 px-3 py-2.5">
                    <p className="font-medium text-foreground text-[11px]">医学教材 · 默沙东诊疗手册</p>
                    <p className="mt-1 text-[11px]">
                      三千多个 PDF 文件，覆盖免疫、感染、癌症、心血管等 26 个医学分类，共生成 28,583 个向量片段。
                    </p>
                    <p className="mt-1 text-[10px] text-muted-foreground/70">
                      版权归属 Merck &amp; Co., Inc. · 仅用于本项目研究目的
                    </p>
                  </div>
                  <div className="rounded-lg border border-border/50 bg-muted/30 px-3 py-2.5">
                    <p className="font-medium text-foreground text-[11px]">问答对 · Huatuo-26M</p>
                    <p className="mt-1 text-[11px]">
                      50,000 条中文医学问答对，教材检索不足时提供补充回答。
                    </p>
                    <p className="mt-1 text-[10px] text-muted-foreground/70">
                      arXiv:2305.01526 · Li et al. 2023
                    </p>
                  </div>
                </div>
              </section>

              {/* AI 模型 */}
              <section>
                <h3 className="font-medium text-foreground mb-1.5">AI 模型</h3>
                <p className="text-xs leading-relaxed">
                  向量化和重排序用的都是北京智源人工智能研究院（BAAI）开源的模型，基于 MIT 协议本地部署。
                </p>
              </section>

              {/* 免责声明 */}
              <section>
                <h3 className="font-medium text-foreground mb-1.5">声明</h3>
                <div className="rounded-lg border-l-3 border-amber-400 bg-amber-50 dark:bg-amber-950/30 px-3 py-2.5 text-[11px] text-amber-800 dark:text-amber-200 leading-relaxed space-y-1.5">
                  <p>本项目为个人学习作品，无商业目的。</p>
                  <p>医学知识更新频繁，系统回答可能存在遗漏或过时之处。涉及诊断、用药、治疗等问题时，请务必咨询专业医师。</p>
                  <p>教材数据版权归原权利人所有。</p>
                </div>
              </section>
            </div>

            {/* Footer */}
            <div className="border-t border-border/50 px-5 py-2.5 text-center text-[10px] text-muted-foreground/50">
              Evibot · 2026
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
