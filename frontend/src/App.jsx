import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { ResourcesProvider } from './context/ResourcesContext'
import AppLayout from './components/layout/AppLayout'
import Dashboard from './pages/Dashboard'
import Library from './pages/Library'
import Search from './pages/Search'
import AddResource from './pages/AddResource'
import Categories from './pages/Categories'
import LibraryHealth from './pages/LibraryHealth'
import Settings from './pages/Settings'
import ResourceDetail from './pages/ResourceDetail'
import Agent from './pages/Agent'
import ShareCapture from './pages/ShareCapture'

// The owner/admin activation-password gate that used to wrap this
// component (checking /setup/status and showing a password/unlock screen
// before rendering anything) has been removed — IdeaOS now opens directly
// into the normal interface. AI provider API keys remain encrypted at
// rest on the backend regardless (see app/security.py); that was always a
// separate concern from this app-level gate.
function App() {
  return (
    <ThemeProvider>
      <ResourcesProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/share" element={<ShareCapture />} />
            <Route element={<AppLayout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/library" element={<Library />} />
              <Route path="/search" element={<Search />} />
              <Route path="/add" element={<AddResource />} />
              <Route path="/categories" element={<Categories />} />
              <Route path="/health" element={<LibraryHealth />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/resource/:id" element={<ResourceDetail />} />
              <Route path="/agent" element={<Agent />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ResourcesProvider>
    </ThemeProvider>
  )
}

export default App
