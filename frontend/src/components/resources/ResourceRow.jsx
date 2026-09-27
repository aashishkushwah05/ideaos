import { useNavigate } from 'react-router-dom'
import { Star, ExternalLink } from 'lucide-react'
import Badge from '../ui/Badge'
import { platformMeta } from '../../utils/platforms'
import { statusMeta } from '../../utils/status'
import { relativeDate } from '../../utils/format'

export default function ResourceRow({ resource, onToggleFavorite }) {
  const navigate = useNavigate()
  const platform = platformMeta(resource.platform)
  const status = statusMeta(resource.status)
  const PlatformIcon = platform.icon

  return (
    <div
      role="link"
      tabIndex={0}
      onClick={() => navigate(`/resource/${resource.id}`)}
      onKeyDown={(e) => {
        if (e.key === 'Enter') navigate(`/resource/${resource.id}`)
      }}
      className="group flex items-center gap-4 rounded-lg border border-transparent px-3 py-3 transition-colors duration-150 hover:border-hairline hover:bg-elevated/50 cursor-pointer"
    >
      <span
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md"
        style={{ background: `${platform.color}1f` }}
      >
        <PlatformIcon size={16} style={{ color: platform.color }} />
      </span>

      <div className="min-w-0 flex-1">
        <p className="truncate text-[14px] font-medium text-text group-hover:text-accent-soft transition-colors">
          {resource.title}
        </p>
        <p className="truncate text-[12.5px] text-text-muted">{resource.originalDescription}</p>
      </div>

      <div className="hidden shrink-0 sm:flex flex-wrap gap-1.5 max-w-[180px]">
        {resource.tags.slice(0, 2).map((tag) => (
          <Badge key={tag} tone="neutral">
            {tag}
          </Badge>
        ))}
      </div>

      <Badge tone={status.tone} className="hidden md:inline-flex shrink-0">
        {status.label}
      </Badge>

      <span className="hidden lg:block w-16 shrink-0 text-right text-[12px] text-text-faint">
        {relativeDate(resource.savedAt)}
      </span>

      <button
        type="button"
        aria-label={resource.favorite ? 'Remove from favorites' : 'Add to favorites'}
        onClick={(e) => {
          e.stopPropagation()
          onToggleFavorite?.(resource.id)
        }}
        className="shrink-0 rounded-md p-1.5 text-text-faint transition-colors duration-150 hover:text-warning"
      >
        <Star size={15} className={resource.favorite ? 'fill-warning text-warning' : ''} />
      </button>

      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation()
          window.open(resource.originalUrl, '_blank', 'noreferrer')
        }}
        className="hidden sm:block shrink-0 rounded-md p-1.5 text-text-faint opacity-0 transition-opacity duration-150 hover:text-accent-soft group-hover:opacity-100"
        aria-label="Open original URL"
      >
        <ExternalLink size={14} />
      </button>
    </div>
  )
}
