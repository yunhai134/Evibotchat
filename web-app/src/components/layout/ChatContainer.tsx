import { useEffect, useRef } from "react"
import { useChatStore } from "@/stores/chat"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ChatMessage } from "@/components/chat/ChatMessage"
import { WelcomeMessage } from "@/components/chat/WelcomeMessage"

export function ChatContainer() {
  const messages = useChatStore((s) => s.messages)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const hasMessages = messages.length > 0

  return (
    <ScrollArea className="flex-1 px-3 py-4 md:px-6 md:py-6">
      <div className="mx-auto max-w-3xl space-y-5">
        {!hasMessages && <WelcomeMessage />}
        {messages.map((msg, idx) => (
          <ChatMessage key={msg.id} index={idx} />
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  )
}