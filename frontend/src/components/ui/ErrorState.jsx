import { AlertTriangle } from 'lucide-react'
import Button from './Button'

export default function ErrorState({
  title = "Couldn't load this",
  description = 'Something went wrong while loading data. Nothing has been changed.',
  onRetry,
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-6">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-danger-dim border border-danger/25">
        <AlertTriangle size={20} className="text-danger" />
      </div>
      <h3 className="text-[15px] font-medium text-text">{title}</h3>
      <p className="mt-1.5 max-w-sm text-[13px] leading-relaxed text-text-muted">{description}</p>
      {onRetry && (
        <div className="mt-5">
          <Button variant="secondary" size="sm" onClick={onRetry}>
            Try again
          </Button>
        </div>
      )}
    </div>
  )
}
