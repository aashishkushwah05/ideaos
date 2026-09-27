import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { LayoutGrid, List, Search as SearchIcon, ArrowUpDown } from 'lucide-react'
import { useResources } from '../context/ResourcesContext'
import { api } from '../utils/api'
import { Input } from '../components/ui/Input'
import SegmentedControl from '../components/ui/SegmentedControl'
import FilterBar from '../components/resources/FilterBar'
import ResourceCard from '../components/resources/ResourceCard'
import ResourceRow from '../components/resources/ResourceRow'
import EmptyState from '../components/ui/EmptyState'
import ErrorState from '../components/ui/ErrorState'
import { SkeletonCard, SkeletonRow } from '../components/ui/Skeleton'

export default function Library() {
  const { resources, facets, loading, error, refresh, toggleFavorite } = useResources()
  const [params] = useSearchParams(); const initialCategory = params.get('category') || 'all'; const collectionId = params.get('collection')
  const [view,setView]=useState('grid'); const [query,setQuery]=useState(''); const [sort,setSort]=useState('newest')
  const [filters,setFilters]=useState({platform:'all',category:initialCategory,status:'all',favorites:'all'})
  const [collectionResources,setCollectionResources]=useState(null)
  useEffect(()=>{if(!collectionId){setCollectionResources(null);return} api.get(`/intelligence/collections/${encodeURIComponent(collectionId)}/items`).then(r=>setCollectionResources(r.items||[])).catch(()=>setCollectionResources([]))},[collectionId])
  const filterDefs=[
    {key:'platform',label:'Platform',options:[{value:'all',label:'All platforms'},...(facets.platforms||[]).map(p=>({value:p,label:p}))]},
    {key:'category',label:'Category',options:[{value:'all',label:'All categories'},...(facets.categories||[]).map(c=>({value:c,label:c}))]},
    {key:'status',label:'Status',options:[{value:'all',label:'All statuses'},{value:'IMPORTABLE',label:'Saved'},{value:'NEEDS_REVIEW',label:'Needs review'},{value:'EXACT_DUPLICATE',label:'Duplicate'}]},
    {key:'favorites',label:'Favorites',options:[{value:'all',label:'All resources'},{value:'favorites',label:'Favorites only'}]},
  ]
  const sourceResources=collectionResources===null?resources:collectionResources.map(r=>({...r,title:r.ai_title||r.original_url,originalUrl:r.original_url,originalDescription:r.original_description||r.ai_summary||'',category:r.ai_category||'Uncategorized',tags:r.ai_tags||[],status:r.import_status?.toLowerCase(),savedAt:r.created_at,favorite:Boolean(r.favorite)}))
  const filtered=useMemo(()=>sourceResources.filter(r=>{
    if(query && !`${r.title} ${r.originalDescription} ${r.tags.join(' ')} ${r.category} ${r.platform}`.toLowerCase().includes(query.toLowerCase())) return false
    if(filters.platform!=='all' && r.platform!==filters.platform) return false
    if(filters.category!=='all' && r.category!==filters.category) return false
    if(filters.status!=='all' && r.import_status!==filters.status) return false
    if(filters.favorites==='favorites'&&!r.favorite) return false
    return true
  }).sort((a,b)=>sort==='az'?a.title.localeCompare(b.title):sort==='oldest'?(a.savedAt>b.savedAt?1:-1):(a.savedAt<b.savedAt?1:-1)),[sourceResources,query,filters,sort])
  if(error&&!resources.length) return <ErrorState onRetry={refresh} description={error}/>
  return <div className="space-y-5">
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div className="max-w-md flex-1"><Input icon={SearchIcon} placeholder="Search your library…" value={query} onChange={e=>setQuery(e.target.value)}/></div><div className="flex items-center gap-2"><div className="relative"><select value={sort} onChange={e=>setSort(e.target.value)} className="h-9.5 appearance-none rounded-lg border border-hairline-strong bg-elevated pl-8 pr-8 text-[13px] text-text outline-none focus:border-accent"><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="az">Title A–Z</option></select><ArrowUpDown size={13} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-text-faint"/></div><SegmentedControl value={view} onChange={setView} options={[{value:'grid',icon:LayoutGrid,label:''},{value:'list',icon:List,label:''}]}/></div></div>
    <div className="flex items-center justify-between gap-3"><FilterBar filters={filterDefs} values={filters} onChange={(key,value)=>setFilters(f=>({...f,[key]:value}))} onClear={()=>setFilters({platform:'all',category:'all',status:'all',favorites:'all'})}/><span className="hidden sm:block text-[12.5px] text-text-faint">{filtered.length} shown</span></div>
    {loading ? <div className={view==='grid'?'grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3':'space-y-2'}>{Array.from({length:6},(_,i)=>view==='grid'?<SkeletonCard key={i}/>:<SkeletonRow key={i}/>)}</div> : filtered.length===0 ? <EmptyState icon={SearchIcon} title="No resources match" description="Try clearing a filter or searching a different term."/> : <div className={view==='grid'?'grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3':'space-y-1'}>{filtered.map(r=>view==='grid'?<ResourceCard key={r.id} resource={r} onToggleFavorite={toggleFavorite}/>:<ResourceRow key={r.id} resource={r} onToggleFavorite={toggleFavorite}/>)}</div>}
  </div>
}
