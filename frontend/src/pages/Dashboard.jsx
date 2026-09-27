import { Link } from 'react-router-dom'
import { Plus, ArrowRight, Star, FolderKanban, HeartPulse, Library, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useResources } from '../context/ResourcesContext'
import { api } from '../utils/api'
import { platformMeta } from '../utils/platforms'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import StatCard from '../components/ui/StatCard'
import ResourceCard from '../components/resources/ResourceCard'
import { SkeletonCard } from '../components/ui/Skeleton'
import ErrorState from '../components/ui/ErrorState'

export default function Dashboard() {
  const { resources, health, loading, error, refresh, toggleFavorite, facets } = useResources()
  const [recommendations, setRecommendations] = useState([])
  const [recError, setRecError] = useState('')

  useEffect(() => {
    api.get('/intelligence/recommendations?limit=4').then((r) => setRecommendations(r.items || [])).catch((e) => setRecError(e.message))
  }, [resources.length])

  if (loading) return <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3"><SkeletonCard /><SkeletonCard /><SkeletonCard /></div>
  if (error) return <ErrorState onRetry={refresh} description={error} />

  const recent = resources.slice(0, 4)
  const favorites = resources.filter((r) => r.favorite).slice(0, 4)
  const platformCounts = resources.reduce((acc, r) => { acc[r.platform] = (acc[r.platform] || 0) + 1; return acc }, {})
  const topPlatforms = Object.entries(platformCounts).sort((a, b) => b[1] - a[1]).slice(0, 6)
  const categoryCount = facets.categories?.length || new Set(resources.map((r) => r.category)).size

  return <div className="space-y-8">
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div><p className="text-[13px] text-text-muted">Your Knowledge OS</p><h2 className="mt-1 font-display text-2xl font-semibold text-text">Welcome back</h2><p className="mt-1.5 text-[13.5px] text-text-muted">{health?.total_resources?.toLocaleString() || 0} resources in your local library{health?.last_import ? ` · last import ${new Date(health.last_import.created_at).toLocaleDateString('en-US',{month:'short',day:'numeric'})}` : ''}</p></div>
      <Link to="/add"><Button><Plus size={15}/>Add Resource</Button></Link>
    </div>

    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <StatCard icon={Library} label="Total resources" value={(health?.total_resources || 0).toLocaleString()} />
      <StatCard icon={Star} label="Favorites" value={resources.filter((r) => r.favorite).length} tone="warning" />
      <StatCard icon={FolderKanban} label="Categories" value={categoryCount} />
      <StatCard icon={HeartPulse} label="Health" value={`${health?.health_score ?? 0}%`} tone={(health?.health_score ?? 0) >= 90 ? 'success' : 'warning'} />
    </div>

    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <section className="lg:col-span-2 space-y-4">
        <div className="flex items-center justify-between"><h3 className="text-[15px] font-medium text-text">Recently saved</h3><Link to="/library" className="flex items-center gap-1 text-[13px] text-text-muted hover:text-accent-soft">View library <ArrowRight size={13}/></Link></div>
        {recent.length ? <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">{recent.map((r) => <ResourceCard key={r.id} resource={r} onToggleFavorite={toggleFavorite}/>)}</div> : <Card className="p-8 text-center text-sm text-text-muted">Your library is empty. Add your first resource.</Card>}
      </section>

      <div className="space-y-6">
        <Card className="p-4"><h3 className="text-[14px] font-medium text-text mb-3">Platform overview</h3><div className="space-y-2.5">{topPlatforms.map(([p,count]) => { const meta=platformMeta(p); const Icon=meta.icon; const pct=Math.round((count/Math.max(resources.length,1))*100); return <div key={p} className="flex items-center gap-2.5"><Icon size={14} style={{color:meta.color}}/><span className="w-20 truncate text-[12.5px] text-text-muted">{meta.label}</span><div className="h-1.5 flex-1 rounded-full bg-elevated overflow-hidden"><div className="h-full rounded-full transition-all duration-700" style={{width:`${pct}%`,background:meta.color}}/></div><span className="w-7 text-right text-[12px] tabular-nums text-text-faint">{count}</span></div>})}</div></Card>
        <Card className="p-4"><div className="flex items-center justify-between mb-3"><h3 className="text-[14px] font-medium text-text">Recommendations</h3><Sparkles size={14} className="text-accent-soft"/></div>{recError ? <p className="text-xs text-danger">{recError}</p> : recommendations.length ? <div className="space-y-2">{recommendations.map((r)=><Link key={r.id} to={`/resource/${r.id}`} className="block rounded-lg px-2 py-2 hover:bg-elevated"><p className="truncate text-[13px] font-medium text-text">{r.title}</p><p className="mt-0.5 line-clamp-2 text-[11.5px] text-text-faint">{r.recommendation_reason}</p></Link>)}</div> : <p className="text-[13px] text-text-muted">Favorite a few resources to unlock personalized recommendations.</p>}</Card>
        <Card className="p-4"><div className="flex items-center justify-between mb-3"><h3 className="text-[14px] font-medium text-text">Library health</h3><Link to="/health" className="text-[12px] text-text-muted hover:text-accent-soft">Details</Link></div><div className="grid grid-cols-2 gap-3 text-[13px]"><div><p className="text-text-faint text-[12px]">Needs review</p><p className="text-warning font-medium">{health?.needs_review || 0}</p></div><div><p className="text-text-faint text-[12px]">AI pending</p><p className="text-text font-medium">{health?.ai_pending || 0}</p></div><div><p className="text-text-faint text-[12px]">Duplicates</p><p className="text-text font-medium">{health?.exact_duplicates || 0}</p></div><div><p className="text-text-faint text-[12px]">Unverified links</p><p className="text-text font-medium">{health?.unverified_links || 0}</p></div></div></Card>
      </div>
    </div>
    {favorites.length > 0 && <section><h3 className="mb-3 text-[15px] font-medium text-text">Favorites</h3><div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">{favorites.map((r)=><ResourceCard key={r.id} resource={r} onToggleFavorite={toggleFavorite}/>)}</div></section>}
  </div>
}
