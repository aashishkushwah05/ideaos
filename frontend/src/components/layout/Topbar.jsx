import { Menu, Search as SearchIcon, Plus } from 'lucide-react'
import { Link } from 'react-router-dom'
import Button from '../ui/Button'

export default function Topbar({ title, subtitle, onOpenMobile, actions }) {
  return (
    <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-hairline bg-canvas/85 backdrop-blur-md px-4 sm:px-6 h-16 shrink-0">
      <button
        onClick={onOpenMobile}
        className="rounded-md p-1.5 text-text-muted hover:text-text lg:hidden"
        aria-label="Open menu"
      >
        <Menu size={20} />
      </button>

      <div className="min-w-0 flex-1">
        <h1 className="truncate font-display text-[17px] font-semibold text-text">{title}</h1>
        {subtitle && <p className="truncate text-[12.5px] text-text-muted">{subtitle}</p>}
      </div>

      <div className="hidden md:flex items-center gap-2">
        <Link to="/search">
          <Button variant="secondary" size="sm">
            <SearchIcon size={14} />
            Search
          </Button>
        </Link>
        <Link to="/add">
          <Button size="sm">
            <Plus size={14} />
            Add Resource
          </Button>
        </Link>
      </div>

      {actions}
    </header>
  )
}
