import { useLottie } from "lottie-react"
import evibotAvatar from "@/animations/evibot-avatar.json"

interface AssistantAvatarProps {
  size?: number
  streaming?: boolean
  className?: string
}

export function AssistantAvatar({ size = 36, streaming = false, className = "" }: AssistantAvatarProps) {
  const { View } = useLottie({
    animationData: evibotAvatar,
    loop: true,
    autoplay: true,
  }, { width: size, height: size })

  return (
    <div
      className={`relative shrink-0 ${className}`}
      style={{ width: size, height: size }}
    >
      {/* Streaming glow ring - outer */}
      {streaming && (
        <>
          <div
            className="absolute -inset-1.5 rounded-full animate-ping"
            style={{
              background: "radial-gradient(circle, rgba(0,212,255,0.3) 0%, transparent 70%)",
            }}
          />
          <div
            className="absolute -inset-1 rounded-full animate-pulse"
            style={{
              boxShadow: "0 0 16px 4px rgba(0,212,255,0.6), 0 0 32px 8px rgba(0,212,255,0.3), 0 0 48px 12px rgba(0,212,255,0.1)",
            }}
          />
        </>
      )}
      {View}
    </div>
  )
}
