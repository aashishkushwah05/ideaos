import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Library,
  Search,
  PlusCircle,
  FolderKanban,
  HeartPulse,
  Settings,
  Bot,
  ChevronsLeft,
  X,
} from 'lucide-react'
import logo from '../../assets/idea-os-logo-full.png'
import { useEffect, useState } from 'react'
import { api } from '../../utils/api'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/library', label: 'Library', icon: Library },
  { to: '/search', label: 'Search', icon: Search },
  { to: '/add', label: 'Add Resource', icon: PlusCircle },
  { to: '/categories', label: 'Categories', icon: FolderKanban },
  { to: '/health', label: 'Library Health', icon: HeartPulse },
  { to: '/agent', label: 'AI Agent', icon: Bot },
  { to: '/settings', label: 'Settings', icon: Settings },
]

function NavItem({ item, collapsed, onNavigate }) {
  const Icon = item.icon
  return (
    <NavLink
      to={item.to}
      end={item.end}
      onClick={onNavigate}
      title={collapsed ? item.label : undefined}
      className={({ isActive }) =>
        `group relative flex items-center gap-3 rounded-lg px-3 h-9.5 text-[13.5px] font-medium transition-colors duration-150
        ${isActive ? 'bg-accent-dim text-accent-soft' : 'text-text-muted hover:text-text hover:bg-elevated'}
        ${collapsed ? 'justify-center px-0' : ''}`
      }
    >
      {({ isActive }) => (
        <>
          {isActive && (
            <span className="absolute left-0 top-1/2 h-4.5 w-[3px] -translate-y-1/2 rounded-full bg-accent" />
          )}
          <Icon size={17} className="shrink-0" />
          {!collapsed && <span className="truncate">{item.label}</span>}
        </>
      )}
    </NavLink>
  )
}

export default function Sidebar({ collapsed, onToggleCollapse, mobileOpen, onCloseMobile }) {
  const [collections, setCollections] = useState([])
  useEffect(() => { api.get('/intelligence/collections').then((r) => setCollections(r.items || [])).catch(() => {}) }, [])
  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-[2px] lg:hidden animate-[fadeIn_0.15s_ease-out]"
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col border-r border-hairline bg-surface
          transition-transform duration-200 ease-out lg:translate-x-0
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:sticky lg:top-0 lg:h-screen
          ${collapsed ? 'w-[76px]' : 'w-[248px]'}`}
      >
        <div className={`flex items-center h-16 shrink-0 border-b border-hairline ${collapsed ? 'justify-center px-2' : 'justify-between px-4'}`}>
          {!collapsed ? (
            <img src={logo} alt="Idea OS" className="h-6 w-auto" />
          ) : (
            <img src={logo} alt="Idea OS" className="h-6 w-6 object-cover object-left" />
          )}
          <button
            onClick={onCloseMobile}
            className="rounded-md p-1.5 text-text-faint hover:text-text lg:hidden"
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-2.5 py-4 space-y-0.5">
          {NAV_ITEMS.map((item) => (
            <NavItem key={item.to} item={item} collapsed={collapsed} onNavigate={onCloseMobile} />
          ))}

          {!collapsed && (
            <div className="pt-5">
              <p className="px-3 text-[11px] font-medium uppercase tracking-wider text-text-faint">
                Collections
              </p>
              <div className="mt-1.5 space-y-0.5">
                {collections.map((c) => (
                  <NavLink
                    key={c.id}
                    to={`/categories?collection=${c.id}`}
                    onClick={onCloseMobile}
                    className="flex items-center justify-between rounded-lg px-3 h-8 text-[13px] text-text-muted transition-colors duration-150 hover:text-text hover:bg-elevated"
                  >
                    <span className="truncate">{c.name}</span>
                    <span className="text-[11px] text-text-faint tabular-nums">{c.count}</span>
                  </NavLink>
                ))}
              </div>
            </div>
          )}
        </nav>

        <div className="hidden lg:flex items-center justify-between border-t border-hairline px-3 h-12 shrink-0">
          {!collapsed && <span className="text-[11px] text-text-faint">Your Knowledge OS</span>}
          <button
            onClick={onToggleCollapse}
            className="rounded-md p-1.5 text-text-faint transition-colors duration-150 hover:text-text hover:bg-elevated"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <ChevronsLeft size={16} className={`transition-transform duration-200 ${collapsed ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </aside>
    </>
  )
}
