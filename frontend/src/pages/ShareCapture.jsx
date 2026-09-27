import { useEffect, useMemo, useState } from 'react'
import { Check, ExternalLink, Loader2, Share2 } from 'lucide-react'
import { useSearchParams, Link } from 'react-router-dom'
import { api } from '../utils/api'

export default function ShareCapture() {
  const [params] = useSearchParams()
  const [status, setStatus] = useState('saving')
  const [message, setMessage] = useState('Saving to your IdeaOS library…')
  const [resourceId, setResourceId] = useState(null)

  const payload = useMemo(() => {
    const url = params.get('url') || (() => {
      const text = params.get('text') || ''
      return text.match(/https?:\/\/[^\s]+/i)?.[0] || ''
    })()
    const text = params.get('text') || params.get('title') || ''
    return { url, description: text, organize_with_ai: true }
  }, [params])

  useEffect(() => {
    let cancelled = false
    if (!payload.url) {
      setStatus('error'); setMessage('No shareable URL was found in the shared content.'); return undefined
    }
    api.post('/resources', payload).then((result) => {
      if (cancelled) return
      if (result.created) {
        setResourceId(result.resource_id); setStatus('success'); setMessage('Saved. IdeaOS will organize it when an AI provider is available.')
      } else if (result.status === 'EXACT_DUPLICATE') {
        setStatus('success'); setMessage('This resource is already in your library.'); setResourceId(result.existing_resource_id)
      } else if (result.requires_confirmation) {
        setStatus('error'); setMessage('This looks like an existing resource variant. Open IdeaOS to review it before saving.')
      } else {
        setStatus('error'); setMessage(result.message || 'IdeaOS could not save this resource.')
      }
    }).catch((error) => {
      if (!cancelled) { setStatus('error'); setMessage(error.message || 'Could not connect to IdeaOS.') }
    })
    return () => { cancelled = true }
  }, [payload])

  return (
    <main className="min-h-screen bg-canvas px-5 py-10 sm:px-8">
      <div className="mx-auto flex min-h-[70vh] max-w-lg items-center justify-center">
        <section className="w-full rounded-3xl border border-hairline bg-surface p-7 text-center shadow-xl sm:p-9">
          <div className="mx-auto mb-5 grid h-14 w-14 place-items-center rounded-2xl bg-accent-dim text-accent-soft">
            {status === 'saving' && <Loader2 className="animate-spin" size={24} />}
            {status === 'success' && <Check size={26} />}
            {status === 'error' && <Share2 size={24} />}
          </div>
          <h1 className="font-display text-xl font-semibold text-text">{status === 'saving' ? 'Saving to IdeaOS' : status === 'success' ? 'Resource saved' : 'Share capture'}</h1>
          <p className="mt-2 text-sm leading-6 text-text-muted">{message}</p>
          {payload.url && <a href={payload.url} target="_blank" rel="noreferrer" className="mx-auto mt-5 flex max-w-full items-center justify-center gap-2 truncate text-xs text-accent-soft hover:underline"><ExternalLink size={13} />{payload.url}</a>}
          <div className="mt-7 flex justify-center gap-2">
            <Link to="/" className="rounded-xl bg-elevated px-4 py-2.5 text-sm font-medium text-text hover:bg-hairline-strong">Open IdeaOS</Link>
            {resourceId && <Link to={`/resource/${resourceId}`} className="rounded-xl bg-accent px-4 py-2.5 text-sm font-medium text-white hover:opacity-90">View resource</Link>}
          </div>
        </section>
      </div>
    </main>
  )
}
