import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api } from '../utils/api'

const ResourcesContext = createContext(null)

function normalizeResource(r) {
  return {
    ...r,
    title: r.ai_title || r.original_url,
    originalUrl: r.original_url,
    originalDescription: r.original_description || r.ai_cleaned_description || '',
    category: r.ai_category || 'Uncategorized',
    subcategory: r.ai_subcategory || '',
    tags: r.ai_tags || [],
    status: r.import_status?.toLowerCase() || 'unique',
    savedAt: r.created_at,
    favorite: Boolean(r.favorite),
  }
}

export function ResourcesProvider({ children }) {
  const [resources, setResources] = useState([])
  const [facets, setFacets] = useState({ categories: [], platforms: [], resource_types: [] })
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const first = await api.get('/resources/search?page=1&page_size=100')
      const pages = [first]
      let page = 1
      while (first.has_more && pages.reduce((sum, item) => sum + (item.items || []).length, 0) < 5000) {
        page += 1
        const next = await api.get(`/resources/search?page=${page}&page_size=100`)
        pages.push(next)
        if (!next.has_more) break
      }
      const [facetResult, healthResult] = await Promise.all([
        api.get('/resources/facets'),
        api.get('/intelligence/health'),
      ])
      setResources(pages.flatMap((result) => result.items || []).map(normalizeResource))
      setFacets(facetResult || {})
      setHealth(healthResult)
    } catch (err) {
      setError(err.message || 'Could not load IdeaOS')
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const toggleFavorite = useCallback(async (id) => {
    const current = resources.find((r) => r.id === id)
    if (!current) return
    const next = !current.favorite
    setResources((prev) => prev.map((r) => r.id === id ? { ...r, favorite: next } : r))
    try { await api.patch(`/resources/${encodeURIComponent(id)}/favorite`, { favorite: next }) }
    catch (err) {
      setResources((prev) => prev.map((r) => r.id === id ? { ...r, favorite: !next } : r))
      setError(err.message || 'Could not update favorite')
    }
  }, [resources])

  const value = useMemo(() => ({ resources, facets, health, loading, error, refresh, toggleFavorite, normalizeResource }), [resources, facets, health, loading, error, refresh, toggleFavorite])
  return <ResourcesContext.Provider value={value}>{children}</ResourcesContext.Provider>
}

export function useResources() {
  const ctx = useContext(ResourcesContext)
  if (!ctx) throw new Error('useResources must be used within ResourcesProvider')
  return ctx
}
