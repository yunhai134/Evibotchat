import { Header } from "@/components/layout/Header"
import { ChatContainer } from "@/components/layout/ChatContainer"
import { ChatInput } from "@/components/chat/ChatInput"
import { EcgBackground } from "@/components/layout/EcgBackground"

export function ChatPage() {
  return (
    <div className="flex min-h-dvh flex-col relative">
      <EcgBackground />
      <div className="relative z-10 flex min-h-dvh flex-col">
        <Header />
        <ChatContainer />
        <ChatInput />
      </div>
    </div>
  )
}