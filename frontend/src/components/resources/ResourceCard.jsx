import { Link } from 'react-router-dom'
import { Star, ExternalLink } from 'lucide-react'
import Card from '../ui/Card'
import Badge from '../ui/Badge'
import { platformMeta } from '../../utils/platforms'
import { statusMeta } from '../../utils/status'
import { relativeDate, hostnameOf } from '../../utils/format'

export default function ResourceCard({ resource, onToggleFavorite }) {
  const platform = platformMeta(resource.platform)
  const status = statusMeta(resource.status || resource.import_status?.toLowerCase())
  const title = resource.title || resource.ai_title || resource.originalUrl
  const description = resource.originalDescription || resource.ai_summary || 'No description saved.'
  const tags = resource.tags || resource.ai_tags || []
  const PlatformIcon = platform.icon

  return (
    <Card interactive className="group relative flex flex-col p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md"
            style={{ background: `${platform.color}1f` }}
          >
            <PlatformIcon size={14} style={{ color: platform.color }} />
          </span>
          <span className="truncate text-[12px] text-text-muted">{hostnameOf(resource.originalUrl)}</span>
        </div>
        <button
          type="button"
          aria-label={resource.favorite ? 'Remove from favorites' : 'Add to favorites'}
          onClick={(e) => {
            e.preventDefault()
            onToggleFavorite?.(resource.id)
          }}
          className="shrink-0 rounded-md p-1 text-text-faint transition-colors duration-150 hover:text-warning"
        >
          <Star size={16} className={resource.favorite ? 'fill-warning text-warning' : ''} />
        </button>
      </div>

      <Link to={`/resource/${resource.id}`} className="mt-3 block">
        <h3 className="text-[14px] font-medium leading-snug text-text line-clamp-2 group-hover:text-accent-soft transition-colors">
          {title}
        </h3>
        <p className="mt-1.5 text-[13px] leading-relaxed text-text-muted line-clamp-2">
          {description}
        </p>
      </Link>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {tags.map((tag) => (
          <Badge key={tag} tone="neutral">
            {tag}
          </Badge>
        ))}
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-hairline pt-3">
        <div className="flex items-center gap-2">
          <Badge tone={status.tone}>{status.label}</Badge>
          <span className="text-[12px] text-text-faint">{relativeDate(resource.savedAt)}</span>
        </div>
        <a
          href={resource.originalUrl}
          target="_blank"
          rel="noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="rounded-md p-1.5 text-text-faint opacity-0 transition-opacity duration-150 hover:text-accent-soft group-hover:opacity-100"
          aria-label="Open original URL"
        >
          <ExternalLink size={14} />
        </a>
      </div>
    </Card>
  )
}
