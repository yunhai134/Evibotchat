import type { Source } from "@/types/stream"
import { Badge } from "@/components/ui/badge"

interface Props {
  source: Source
}

export function SourceBadge({ source }: Props) {
  return (
    <Badge variant="secondary" className="gap-1 text-xs">
      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      {source.source} · p.{source.page}
    </Badge>
  )
}