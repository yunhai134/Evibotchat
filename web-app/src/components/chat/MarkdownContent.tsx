import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeRaw from "rehype-raw"

interface Props {
  content: string
}

export function MarkdownContent({ content }: Props) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw]}
      components={{
        h1: ({ children }) => (
          <h1 className="text-lg font-extrabold text-foreground mt-4 mb-2 pb-1 border-b border-border/50">
            {children}
          </h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-base font-bold text-foreground mt-3 mb-2 flex items-center gap-2">
            <span className="w-1 h-4 rounded-full bg-primary/60" />
            {children}
          </h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-sm font-bold text-foreground mt-2.5 mb-1.5">
            {children}
          </h3>
        ),
        p: ({ children }) => (
          <p className="text-sm font-medium leading-relaxed text-foreground mb-2 last:mb-0">
            {children}
          </p>
        ),
        ul: ({ children }) => (
          <ul className="space-y-1.5 my-2 ml-1">
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol className="space-y-1.5 my-2 ml-1 list-decimal list-inside">
            {children}
          </ol>
        ),
        li: ({ children }) => (
          <li className="text-sm font-medium text-foreground flex items-start gap-2">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/50" />
            <span>{children}</span>
          </li>
        ),
        strong: ({ children }) => (
          <strong className="font-bold text-foreground">
            {children}
          </strong>
        ),
        blockquote: ({ children }) => (
          <blockquote className="border-l-3 border-amber-400/60 bg-amber-50/50 dark:bg-amber-950/20 pl-3 py-1.5 pr-2 my-2 rounded-r-md text-sm font-medium text-foreground italic">
            {children}
          </blockquote>
        ),
        hr: () => (
          <hr className="my-3 border-border/40" />
        ),
        code: ({ children }) => (
          <code className="px-1.5 py-0.5 rounded bg-muted text-xs font-mono font-semibold text-primary">
            {children}
          </code>
        ),
        pre: ({ children }) => (
          <pre className="bg-muted/80 rounded-lg p-3 my-2 overflow-x-auto text-xs font-medium">
            {children}
          </pre>
        ),
        a: ({ href, children }) => (
          <a href={href} className="font-medium text-primary underline underline-offset-2 hover:text-primary/80 transition-colors">
            {children}
          </a>
        ),
        table: ({ children }) => (
          <div className="overflow-x-auto my-2">
            <table className="w-full text-xs border-collapse">
              {children}
            </table>
          </div>
        ),
        thead: ({ children }) => (
          <thead className="bg-muted/80">
            {children}
          </thead>
        ),
        th: ({ children }) => (
          <th className="px-3 py-2 text-left font-bold text-foreground border-b border-border">
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="px-3 py-2 font-medium text-foreground border-b border-border/50">
            {children}
          </td>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  )
}