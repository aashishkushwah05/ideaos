import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import Footer from './Footer'
import MobileNav from './MobileNav'

const PAGE_META = {
  '/': { title: 'Dashboard', subtitle: 'A quick look at your knowledge library' },
  '/library': { title: 'Resource Library', subtitle: 'Browse and manage everything you\u2019ve saved' },
  '/search': { title: 'Search', subtitle: 'Find anything across your saved resources' },
  '/add': { title: 'Add Resource', subtitle: 'Save a new link to your library' },
  '/categories': { title: 'Categories & Collections', subtitle: 'Browse resources by topic and platform' },
  '/health': { title: 'Library Health', subtitle: 'Data integrity at a glance' },
  '/settings': { title: 'Settings', subtitle: 'Local preferences for this device' },
}

function metaFor(pathname) {
  if (PAGE_META[pathname]) return PAGE_META[pathname]
  if (pathname.startsWith('/resource/')) return { title: 'Resource Detail', subtitle: '' }
  return { title: 'Idea OS', subtitle: '' }
}

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()
  const meta = metaFor(location.pathname)

  return (
    <div className="flex min-h-screen bg-canvas">
      <Sidebar
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed((c) => !c)}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar title={meta.title} subtitle={meta.subtitle} onOpenMobile={() => setMobileOpen(true)} />

        <main className="flex-1 px-4 pb-24 pt-5 sm:px-6 sm:py-6 lg:pb-6">
          <div className="mx-auto w-full max-w-[1200px]">
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.16, ease: 'easeOut' }}
              >
                <Outlet />
              </motion.div>
            </AnimatePresence>
          </div>
        </main>

        <Footer />
        <MobileNav />
      </div>
    </div>
  )
}
