import { NavLink, useLocation } from 'react-router-dom'
import { Bot, Library, Plus, Search, Settings } from 'lucide-react'

const ITEMS = [
  { to: '/', label: 'Home', icon: Library, end: true },
  { to: '/search', label: 'Search', icon: Search },
  { to: '/add', label: 'Add', icon: Plus, primary: true },
  { to: '/agent', label: 'Agent', icon: Bot },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export default function MobileNav() {
  const location = useLocation()
  return (
    <nav aria-label="Mobile navigation" className="fixed inset-x-0 bottom-0 z-40 border-t border-hairline bg-surface/95 px-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2 backdrop-blur-xl lg:hidden">
      <div className="mx-auto flex max-w-md items-end justify-around gap-1">
        {ITEMS.map(({ to, label, icon: Icon, end, primary }) => {
          const active = end ? location.pathname === to : location.pathname.startsWith(to)
          return (
            <NavLink key={to} to={to} end={end} className={`flex min-w-14 flex-1 flex-col items-center justify-center gap-1 rounded-xl py-1.5 text-[10px] font-medium transition-colors ${active ? 'text-accent-soft' : 'text-text-faint hover:text-text'} ${primary ? 'relative -mt-4' : ''}`}>
              <span className={primary ? 'grid h-11 w-11 place-items-center rounded-full border border-accent/40 bg-accent text-white shadow-lg' : ''}>
                <Icon size={primary ? 20 : 18} />
              </span>
              <span>{label}</span>
            </NavLink>
          )
        })}
      </div>
    </nav>
  )
}
