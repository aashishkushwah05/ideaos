import { useState } from 'react'
import { motion } from 'framer-motion'
import { Bot, Send, Sparkles, Search, Map, ShieldCheck, Loader2, CheckCircle2 } from 'lucide-react'
import { api } from '../utils/api'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'

const suggestions = [
  { icon: Search, text: 'Find my resources about AI agents' },
  { icon: Map, text: 'Create a roadmap for learning Next.js' },
  { icon: Sparkles, text: 'What should I learn next?' },
  { icon: ShieldCheck, text: 'Find duplicate resources in my library' },
]

export default function Agent() {
  const [task, setTask] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [confirming, setConfirming] = useState(null)

  async function run(confirmed = false, overrideTask = null) {
    const prompt = (overrideTask ?? task).trim()
    if (!prompt || loading) return
    setLoading(true); setError('')
    setMessages((m) => [...m, { role: 'user', text: prompt }])
    try {
      const result = await api.post('/agent/run', { task: prompt, max_steps: 8, confirmed })
      setMessages((m) => [...m, { role: 'agent', result }])
      const writeStep = (result.steps || []).find((s) => s.result?.status === 'CONFIRMATION_REQUIRED')
      setConfirming(writeStep ? { prompt, result } : null)
      setTask('')
    } catch (e) { setError(e.message || 'Agent request failed') }
    finally { setLoading(false) }
  }

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6">
      <div>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-dim text-accent"><Bot size={21} /></div>
          <div><h1 className="text-xl font-semibold tracking-tight text-text">IdeaOS AI Agent</h1><p className="text-sm text-text-muted">Ask questions and work with your knowledge library.</p></div>
        </div>
      </div>

      {messages.length === 0 && (
        <Card className="overflow-hidden p-0">
          <div className="border-b border-hairline px-5 py-5 sm:px-7">
            <p className="text-sm font-medium text-text">What do you want to do?</p>
            <p className="mt-1 text-xs text-text-muted">The agent can search, connect, analyze and build plans from your saved knowledge.</p>
          </div>
          <div className="grid gap-2 p-4 sm:grid-cols-2 sm:p-5">
            {suggestions.map(({ icon: Icon, text }) => <button key={text} onClick={() => { setTask(text); run(false, text) }} className="flex items-center gap-3 rounded-xl border border-hairline bg-surface px-4 py-3 text-left text-sm text-text transition hover:border-accent/40 hover:bg-elevated"><Icon size={17} className="shrink-0 text-accent" /><span>{text}</span></button>)}
          </div>
        </Card>
      )}

      <div className="space-y-3">
        {messages.map((m, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className={m.role === 'user' ? 'ml-auto max-w-[90%] rounded-2xl rounded-br-md bg-accent px-4 py-3 text-sm text-white sm:max-w-[70%]' : ''}>
            {m.role === 'user' ? m.text : <Card className="p-4 sm:p-5"><div className="flex items-center gap-2 text-xs font-medium text-accent"><Bot size={14} /> IdeaOS Agent</div><p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-text">{m.result?.message}</p>{m.result?.steps?.length > 0 && <div className="mt-4 space-y-2 border-t border-hairline pt-3">{m.result.steps.map((s, j) => <div key={j} className="flex items-start gap-2 text-xs text-text-muted"><CheckCircle2 size={14} className={s.status === 'ERROR' ? 'text-danger' : 'text-success'} /><span>{s.tool}{s.result?.count != null ? ` · ${s.result.count} results` : ''}</span></div>)}</div>}</Card>}
          </motion.div>
        ))}
      </div>

      {confirming && <Card className="border-accent/30 p-4"><p className="text-sm font-medium text-text">This action will change your library.</p><p className="mt-1 text-xs text-text-muted">Do you want IdeaOS to apply the proposed action?</p><div className="mt-3 flex gap-2"><Button onClick={() => { setConfirming(null); run(true, confirming.prompt) }}>Confirm</Button><Button variant="secondary" onClick={() => setConfirming(null)}>Cancel</Button></div></Card>}

      {error && <p className="text-sm text-danger">{error}</p>}

      <div className="sticky bottom-4">
        <Card className="p-2 shadow-lg"><div className="flex items-end gap-2"><textarea value={task} onChange={(e) => setTask(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); run() } }} rows={1} maxLength={2000} placeholder="Ask anything about your library…" className="min-h-11 flex-1 resize-none bg-transparent px-3 py-3 text-sm text-text outline-none placeholder:text-text-faint" /><Button onClick={() => run()} disabled={!task.trim() || loading} aria-label="Send">{loading ? <Loader2 size={17} className="animate-spin" /> : <Send size={17} />}</Button></div><div className="px-3 pb-1 text-[10px] text-text-faint">Enter to send · Shift+Enter for a new line</div></Card>
      </div>
    </div>
  )
}
