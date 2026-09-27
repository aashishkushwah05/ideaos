import { useEffect, useState } from 'react'
import { Moon, Sun, Laptop, ShieldCheck, FolderOpen, Bot, RefreshCw, CheckCircle2, AlertTriangle, CircleSlash2, Trash2, KeyRound } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import Card from '../components/ui/Card'
import SegmentedControl from '../components/ui/SegmentedControl'
import Switch from '../components/ui/Switch'
import Button from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { api } from '../utils/api'

const PROVIDER_DISPLAY_NAMES = {
  openai: 'OpenAI', kimi: 'Kimi', nvidia: 'NVIDIA', gemini: 'Gemini',
  claude: 'Claude', ollama: 'Ollama', custom: 'Custom',
}
function providerDisplayName(name) { return PROVIDER_DISPLAY_NAMES[name?.toLowerCase()] || name }

function ProviderRow({ provider, secret, onTest, testing, onRemove, removing }) {
  const status = provider.enabled ? 'Active' : provider.configured ? 'Configured' : 'Not configured'
  const Icon = provider.enabled ? CheckCircle2 : provider.configured ? AlertTriangle : CircleSlash2
  return (
    <div className="flex flex-col gap-3 border-t border-hairline py-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <Bot size={15} className="text-accent" />
          <span className="text-sm font-medium text-text">{providerDisplayName(provider.name)}</span>
          <span className="flex items-center gap-1 text-[11px] text-text-faint"><Icon size={12} /> {status}</span>
        </div>
        <p className="mt-1 break-all text-xs text-text-muted">{provider.model || 'No model configured'}{provider.endpoint ? ` · ${provider.endpoint}` : ''}</p>
        {provider.task_roles?.length > 0 && <p className="mt-1 text-[11px] text-text-faint">Tasks: {provider.task_roles.join(', ')}</p>}
        {secret?.configured && (
          <p className="mt-1.5 flex items-center gap-1.5 text-[11px] text-text-faint">
            <KeyRound size={11} /> Saved credential: <span className="font-mono text-text-muted">{secret.masked}</span>
          </p>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {secret?.configured && (
          <Button size="sm" variant="ghost" disabled={removing} onClick={() => onRemove(provider.name)} title="Remove saved credential">
            {removing ? <RefreshCw size={14} className="animate-spin" /> : <Trash2 size={14} />}
          </Button>
        )}
        <Button size="sm" variant="secondary" disabled={!provider.configured || testing} onClick={() => onTest(provider.name)}>
          {testing ? <RefreshCw size={14} className="animate-spin" /> : 'Test connection'}
        </Button>
      </div>
    </div>
  )
}

export default function Settings() {
  const { mode, setMode } = useTheme()
  const [autoOrganize, setAutoOrganize] = useState(false)
  const [confirmBeforeImport, setConfirmBeforeImport] = useState(true)
  const [keepInvalidVisible, setKeepInvalidVisible] = useState(true)
  const [sourceFolder, setSourceFolder] = useState('backend/data/source_imports')
  const [providers, setProviders] = useState([])
  const [providerError, setProviderError] = useState('')
  const [testing, setTesting] = useState('')
  const [testResult, setTestResult] = useState(null)
  const [providerKey, setProviderKey] = useState({ provider: '', api_key: '' })
  const [secretSaved, setSecretSaved] = useState('')
  const [secrets, setSecrets] = useState({}) // { [providerName]: { configured, masked } }
  const [removing, setRemoving] = useState('')

  async function loadProviders() {
    setProviderError('')
    try {
      const list = (await api.get('/ai/providers')).providers || []
      setProviders(list)
      // Masked credential state is fetched separately per provider — the
      // backend never includes the key (even masked) in the /ai/providers
      // listing itself, so this is an intentional second, narrow request.
      const entries = await Promise.all(
        list.map(async (p) => {
          try { return [p.name, await api.get(`/setup/providers/secret/${encodeURIComponent(p.name)}`)] }
          catch { return [p.name, { configured: false, masked: null }] }
        })
      )
      setSecrets(Object.fromEntries(entries))
    } catch (e) { setProviderError(e.message || 'Could not load provider status') }
  }
  useEffect(() => { loadProviders() }, [])

  async function saveProviderKey(e) { e.preventDefault(); setSecretSaved('')
    try {
      await api.post('/setup/providers/secret', providerKey)
      setSecretSaved(`Saved ${providerKey.provider} credentials securely on this device.`)
      setProviderKey({provider:'', api_key:''})
      loadProviders() // refresh masked view + status for the provider just saved
    }
    catch (e) { setSecretSaved(e.message || 'Could not save credentials.') }
  }

  async function removeProviderSecret(name) {
    setRemoving(name)
    try {
      await api.delete(`/setup/providers/secret/${encodeURIComponent(name)}`)
      setSecrets((prev) => ({ ...prev, [name]: { configured: false, masked: null } }))
      loadProviders() // status (enabled/configured) may also change once removed
    } catch (e) {
      setProviderError(e.message || `Could not remove the ${name} credential.`)
    } finally {
      setRemoving('')
    }
  }

  async function testProvider(name) {
    setTesting(name); setTestResult(null)
    try { setTestResult(await api.post(`/ai/providers/${encodeURIComponent(name)}/test`, { task: 'agent' })) }
    catch (e) { setTestResult({ status: 'ERROR', message: e.message }) }
    finally { setTesting('') }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <Card className="p-5">
        <h3 className="mb-1 text-[14px] font-medium text-text">Appearance</h3>
        <p className="mb-4 text-[12.5px] text-text-muted">Choose how IdeaOS looks on this device.</p>
        <SegmentedControl value={mode} onChange={setMode} options={[{ value: 'light', label: 'Light', icon: Sun }, { value: 'dark', label: 'Dark', icon: Moon }, { value: 'system', label: 'System', icon: Laptop }]} />
      </Card>

      <Card className="p-5">
        <h3 className="mb-1 text-[14px] font-medium text-text">AI providers</h3>
        <p className="mb-3 text-[12.5px] text-text-muted">Connect AI providers on the local backend. API keys are never displayed by IdeaOS.</p>
        {providerError && <p className="mb-3 rounded-lg border border-danger/25 bg-danger-dim p-3 text-xs text-danger">{providerError}</p>}
        {testResult && <div className={`mb-3 rounded-lg border p-3 text-xs ${testResult.status === 'HEALTHY' ? 'border-success/25 bg-success-dim text-success' : 'border-danger/25 bg-danger-dim text-danger'}`}>{testResult.status}: {testResult.message || testResult.response || 'Connection checked.'}</div>}
        {providers.length === 0 && !providerError && <p className="py-4 text-xs text-text-faint">Loading provider status…</p>}
        {providers.map((provider) => (
          <ProviderRow
            key={provider.name}
            provider={provider}
            secret={secrets[provider.name]}
            onTest={testProvider}
            testing={testing === provider.name}
            onRemove={removeProviderSecret}
            removing={removing === provider.name}
          />
        ))}
        <form onSubmit={saveProviderKey} className="mt-5 border-t border-hairline pt-5 space-y-3">
          <div><h4 className="text-sm font-medium text-text">Secure provider credentials</h4><p className="mt-1 text-xs text-text-muted">Store a provider API key encrypted by your IdeaOS access password. The key is never rendered back to the browser.</p></div>
          <div className="grid gap-3 sm:grid-cols-2"><select value={providerKey.provider} onChange={e=>setProviderKey({...providerKey,provider:e.target.value})} className="h-10 rounded-lg border border-hairline bg-surface px-3 text-sm text-text"><option value="">Choose provider</option>{providers.map(p=><option key={p.name} value={p.name}>{providerDisplayName(p.name)}</option>)}</select><Input type="password" value={providerKey.api_key} onChange={e=>setProviderKey({...providerKey,api_key:e.target.value})} placeholder="API key" autoComplete="off" /></div>
          <Button type="submit" size="sm" disabled={!providerKey.provider || !providerKey.api_key}>Save encrypted key</Button>
          {secretSaved && <p className="text-xs text-text-muted">{secretSaved}</p>}
        </form>
        <p className="mt-3 text-[11px] text-text-faint">Environment variables remain supported for developer setups. Local encrypted credentials always take precedence.</p>
      </Card>

      <Card className="p-5">
        <h3 className="mb-1 text-[14px] font-medium text-text">Import preferences</h3>
        <p className="mb-2 text-[12.5px] text-text-muted">These control how future imports behave. They don’t change anything already in your library.</p>
        <div className="divide-y divide-hairline">
          <Switch checked={confirmBeforeImport} onChange={setConfirmBeforeImport} label="Confirm before importing" description="Always show the reconciliation report before anything is added." />
          <Switch checked={keepInvalidVisible} onChange={setKeepInvalidVisible} label="Keep invalid URLs visible" description="Show invalid/malformed entries in Library Health instead of hiding them." />
          <Switch checked={autoOrganize} onChange={setAutoOrganize} label="Auto-organize new resources" description="When an AI provider is connected, suggest tags and categories automatically." />
        </div>
        <div className="mt-4">
          <label className="mb-1.5 block text-[13px] font-medium text-text">Source import folder</label>
          <Input icon={FolderOpen} value={sourceFolder} onChange={(e) => setSourceFolder(e.target.value)} />
          <p className="mt-1.5 text-[12px] text-text-faint">Where IdeaOS looks for new CSV/DOCX files to import.</p>
        </div>
      </Card>

      <Card className="border-success/25 bg-success-dim p-5">
        <div className="flex items-start gap-3"><ShieldCheck size={18} className="mt-0.5 shrink-0 text-success" /><div><h3 className="text-[14px] font-medium text-text">Your data stays on this device.</h3><p className="mt-1 text-[12.5px] leading-relaxed text-text-muted">IdeaOS runs locally. Your library and preferences stay local unless you explicitly connect an AI provider; only the data needed for that AI task is sent to the configured provider.</p></div></div>
      </Card>
    </div>
  )
}
