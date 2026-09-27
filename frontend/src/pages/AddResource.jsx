import { useRef, useState } from 'react'
import {
  Link2, FileText, Image as ImageIcon, FileType2, Package,
  CheckCircle2, AlertTriangle, Loader2, XCircle, RotateCcw, ArrowLeft, Upload,
} from 'lucide-react'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import { Input, Textarea } from '../components/ui/Input'
import { api } from '../utils/api'

const RESOURCE_TYPES = [
  { id: 'LINK', label: 'Link', icon: Link2, description: 'Save a URL from Instagram, YouTube, GitHub, X, LinkedIn, websites, and more.' },
  { id: 'PDF', label: 'PDF', icon: FileText, description: 'Save an important PDF locally.', accept: '.pdf' },
  { id: 'IMAGE', label: 'Image', icon: ImageIcon, description: 'Save screenshots and images.', accept: '.png,.jpg,.jpeg,.webp,.gif,image/*' },
  { id: 'DOCUMENT', label: 'Document', icon: FileType2, description: 'Save documents, notes, and text files.', accept: '.docx,.txt,.md' },
  { id: 'FILE', label: 'File', icon: Package, description: 'Save another useful local file.', accept: '.csv,.json,.zip' },
]

function detectPlatform(url) {
  try {
    const host = new URL(url).hostname.replace(/^www\./, '').toLowerCase()
    if (host.includes('instagram.com')) return 'Instagram'
    if (host.includes('youtube.com') || host.includes('youtu.be')) return 'YouTube'
    if (host.includes('linkedin.com')) return 'LinkedIn'
    if (host.includes('github.com')) return 'GitHub'
    if (host.includes('twitter.com') || host.includes('x.com')) return 'X/Twitter'
    if (host.includes('facebook.com')) return 'Facebook'
    return 'Website'
  } catch {
    return null
  }
}

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function AddResource() {
  const [selectedType, setSelectedType] = useState(null)

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h2 className="font-display text-xl font-semibold text-text">Add a resource</h2>
        <p className="mt-1 text-[13.5px] text-text-muted">
          Save something into your local IdeaOS library. Everything is validated and checked for
          duplicates before it's stored — originals are always preserved exactly as given.
        </p>
      </div>

      {!selectedType ? (
        <TypeChooser onSelect={setSelectedType} />
      ) : selectedType === 'LINK' ? (
        <LinkForm onBack={() => setSelectedType(null)} />
      ) : (
        <FileForm
          key={selectedType}
          typeConfig={RESOURCE_TYPES.find((t) => t.id === selectedType)}
          onBack={() => setSelectedType(null)}
        />
      )}
    </div>
  )
}

function TypeChooser({ onSelect }) {
  return (
    <div>
      <p className="mb-3 text-[13px] font-medium text-text-muted">What do you want to save?</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {RESOURCE_TYPES.map((type) => {
          const Icon = type.icon
          return (
            <button key={type.id} type="button" onClick={() => onSelect(type.id)} className="text-left">
              <Card interactive className="flex h-full flex-col items-start gap-2.5 p-4">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent-dim">
                  <Icon size={17} className="text-accent-soft" />
                </span>
                <span className="text-[14px] font-medium text-text">{type.label}</span>
                <span className="text-[12px] leading-snug text-text-muted">{type.description}</span>
              </Card>
            </button>
          )
        })}
      </div>
    </div>
  )
}

function BackLink({ onBack, label }) {
  return (
    <button type="button" onClick={onBack} className="mb-3 flex items-center gap-1.5 text-[13px] text-text-muted transition-colors hover:text-text">
      <ArrowLeft size={14} /> {label}
    </button>
  )
}

// ---------------------------------------------------------------------------
// LINK flow — same validate → check-duplicate → save pipeline as before.
// Only change from the previous version: uses the shared `api` client (which
// attaches the owner-access bearer token) instead of a local fetch helper
// that silently omitted it — that omission meant every request here 401'd
// once an owner password was set up, which is why Add Resource previously
// stopped working after activation.
// ---------------------------------------------------------------------------
function LinkForm({ onBack }) {
  const [url, setUrl] = useState('')
  const [description, setDescription] = useState('')
  const [touched, setTouched] = useState(false)
  const [phase, setPhase] = useState('idle') // idle | checking | duplicate | review | saving | success | error
  const [result, setResult] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')

  const urlError = touched && url.trim() === ''
    ? 'A URL is required.'
    : touched && !/^https?:\/\/[^\s]+$/i.test(url.trim())
      ? 'Enter a full URL, starting with http:// or https://.'
      : null

  const platform = url && !urlError ? detectPlatform(url) : null

  const checkAndAdd = async (confirmPossibleDuplicate = false) => {
    setTouched(true)
    if (urlError) return

    setPhase('checking')
    setErrorMessage('')
    setResult(null)
    try {
      const checked = await api.post('/resources/check', { url: url.trim(), description: description || null })

      if (checked.status === 'EXACT_DUPLICATE') { setResult(checked); setPhase('duplicate'); return }
      if (checked.status === 'POSSIBLE_DUPLICATE' && !confirmPossibleDuplicate) { setResult(checked); setPhase('review'); return }

      setPhase('saving')
      const saved = await api.post('/resources', {
        url: url.trim(),
        description: description || null,
        organize_with_ai: false,
        confirm_possible_duplicate: confirmPossibleDuplicate,
      })

      if (saved.status === 'EXACT_DUPLICATE') { setResult(saved); setPhase('duplicate'); return }
      if (saved.status === 'POSSIBLE_DUPLICATE' || saved.requires_confirmation) { setResult(saved); setPhase('review'); return }

      setResult(saved)
      setPhase('success')
    } catch (error) {
      setErrorMessage(error.message || 'Something went wrong while saving this resource.')
      setPhase('error')
    }
  }

  const reset = () => {
    setUrl(''); setDescription(''); setTouched(false); setPhase('idle'); setResult(null); setErrorMessage('')
  }

  return (
    <div>
      {phase === 'idle' && <BackLink onBack={onBack} label="Choose a different type" />}
      <Card className="p-5">
        {phase === 'success' ? (
          <SuccessState message="Your resource is now stored in the local SQLite library. Original data was not rewritten." idLabel={result?.resource_id ? `ID: ${result.resource_id}` : null} onReset={reset} />
        ) : phase === 'duplicate' ? (
          <DuplicateState
            message="Nothing was overwritten and no second copy was created. Your existing resource remains untouched."
            detail={result?.existing_resource_id ? `Existing resource: ${result.existing_resource_id}` : null}
            onReset={reset} onBack={() => setPhase('idle')}
          />
        ) : phase === 'review' ? (
          <ReviewState
            detail={result?.existing_url ? `Existing: ${result.existing_url}` : null}
            onReset={reset} onConfirm={() => checkAndAdd(true)} onBack={() => setPhase('idle')}
          />
        ) : phase === 'error' ? (
          <ErrorState message={errorMessage} onRetry={() => setPhase('idle')} />
        ) : (
          <form onSubmit={(event) => { event.preventDefault(); checkAndAdd(false) }} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-text">URL</label>
              <Input
                icon={Link2}
                placeholder="https://www.instagram.com/reel/…"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                onBlur={() => setTouched(true)}
                error={!!urlError}
                disabled={phase === 'checking' || phase === 'saving'}
                autoComplete="url"
                inputMode="url"
              />
              {urlError && <p className="mt-1.5 text-[12.5px] text-danger">{urlError}</p>}
              {platform && <div className="mt-1.5"><Badge tone="accent">Detected: {platform}</Badge></div>}
            </div>

            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-text">Description</label>
              <Textarea
                rows={3}
                placeholder="A short note about why this is worth keeping…"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                disabled={phase === 'checking' || phase === 'saving'}
                maxLength={10000}
              />
              <p className="mt-1.5 text-[12px] text-text-faint">Optional — preserved exactly as written.</p>
            </div>

            <div className="flex items-center justify-end pt-1">
              <Button type="submit" disabled={phase === 'checking' || phase === 'saving'}>
                {phase === 'checking' || phase === 'saving' ? (
                  <><Loader2 size={15} className="animate-spin" /> {phase === 'saving' ? 'Saving resource…' : 'Checking library…'}</>
                ) : 'Check & add resource'}
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  )
}

// ---------------------------------------------------------------------------
// PDF / IMAGE / DOCUMENT / FILE flow — new capture path, backed by
// POST /resources/file. Supports drag-and-drop on desktop and a plain file
// picker everywhere (including mobile), upload progress, and the same
// success/duplicate/error state language as the Link flow.
// ---------------------------------------------------------------------------
function FileForm({ typeConfig, onBack }) {
  const [file, setFile] = useState(null)
  const [description, setDescription] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const [phase, setPhase] = useState('idle') // idle | uploading | success | duplicate | error
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')
  const inputRef = useRef(null)
  const Icon = typeConfig.icon

  const pickFile = (selected) => {
    if (selected) setFile(selected)
  }

  const upload = async () => {
    if (!file) return
    setPhase('uploading')
    setProgress(0)
    setErrorMessage('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      if (description.trim()) formData.append('description', description.trim())
      const response = await api.upload('/resources/file', formData, { onProgress: setProgress })

      if (response.status === 'EXACT_DUPLICATE') { setResult(response); setPhase('duplicate'); return }
      setResult(response)
      setPhase('success')
    } catch (error) {
      setErrorMessage(error.message || 'Something went wrong while saving this file.')
      setPhase('error')
    }
  }

  const reset = () => {
    setFile(null); setDescription(''); setPhase('idle'); setProgress(0); setResult(null); setErrorMessage('')
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div>
      {phase === 'idle' && <BackLink onBack={onBack} label="Choose a different type" />}
      <Card className="p-5">
        {phase === 'success' ? (
          <SuccessState
            message="Your file is stored locally and tracked in the library. It was not uploaded to any cloud service."
            idLabel={result?.resource_id ? `ID: ${result.resource_id}` : null}
            onReset={reset}
          />
        ) : phase === 'duplicate' ? (
          <DuplicateState
            message="A file with identical content is already in your library. Nothing was uploaded twice."
            detail={result?.existing_resource_id ? `Existing resource: ${result.existing_resource_id}` : null}
            onReset={reset} onBack={reset}
          />
        ) : phase === 'error' ? (
          <ErrorState message={errorMessage} onRetry={reset} />
        ) : (
          <form onSubmit={(event) => { event.preventDefault(); upload() }} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-text">{typeConfig.label}</label>
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => {
                  e.preventDefault(); setDragOver(false)
                  pickFile(e.dataTransfer.files?.[0])
                }}
                onClick={() => inputRef.current?.click()}
                className={`flex cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors duration-150
                  ${dragOver ? 'border-accent bg-accent-dim' : 'border-hairline-strong bg-elevated hover:border-accent/40'}`}
              >
                <input
                  ref={inputRef}
                  type="file"
                  accept={typeConfig.accept}
                  className="hidden"
                  disabled={phase === 'uploading'}
                  onChange={(e) => pickFile(e.target.files?.[0])}
                />
                {file ? (
                  <>
                    <Icon size={22} className="text-accent-soft" />
                    <span className="max-w-full truncate text-[13.5px] font-medium text-text">{file.name}</span>
                    <span className="text-[12px] text-text-faint">{formatBytes(file.size)}</span>
                  </>
                ) : (
                  <>
                    <Upload size={20} className="text-text-faint" />
                    <span className="text-[13px] text-text-muted">
                      <span className="hidden sm:inline">Drag and drop, or </span>tap to choose a file
                    </span>
                    <span className="text-[11px] text-text-faint">Up to 50 MB</span>
                  </>
                )}
              </div>
              {file && (
                <button type="button" onClick={(e) => { e.stopPropagation(); reset() }} className="mt-1.5 text-[12px] text-text-faint hover:text-danger">
                  Remove file
                </button>
              )}
            </div>

            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-text">Description</label>
              <Textarea
                rows={3}
                placeholder="A short note about this file…"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                disabled={phase === 'uploading'}
                maxLength={10000}
              />
              <p className="mt-1.5 text-[12px] text-text-faint">Optional — preserved exactly as written.</p>
            </div>

            {phase === 'uploading' && (
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-elevated">
                <div className="h-full rounded-full bg-accent transition-all duration-150" style={{ width: `${progress}%` }} />
              </div>
            )}

            <div className="flex items-center justify-end pt-1">
              <Button type="submit" disabled={!file || phase === 'uploading'}>
                {phase === 'uploading' ? (
                  <><Loader2 size={15} className="animate-spin" /> Saving file… {progress > 0 ? `${progress}%` : ''}</>
                ) : `Save ${typeConfig.label.toLowerCase()}`}
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Shared result states (used by both flows)
// ---------------------------------------------------------------------------
function SuccessState({ message, idLabel, onReset }) {
  return (
    <div className="flex flex-col items-center text-center py-4">
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-success-dim border border-success/25">
        <CheckCircle2 size={22} className="text-success" />
      </div>
      <h3 className="text-[15px] font-medium text-text">Resource saved</h3>
      <p className="mt-1.5 max-w-sm text-[13px] leading-relaxed text-text-muted">{message}</p>
      {idLabel && <p className="mt-2 text-[11px] text-text-faint break-all">{idLabel}</p>}
      <Button variant="secondary" size="sm" className="mt-4" onClick={onReset}><RotateCcw size={14} /> Add another</Button>
    </div>
  )
}

function DuplicateState({ message, detail, onReset, onBack }) {
  return (
    <div className="flex flex-col items-center text-center py-4">
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-elevated border border-hairline-strong">
        <AlertTriangle size={22} className="text-text-muted" />
      </div>
      <h3 className="text-[15px] font-medium text-text">Already in your library</h3>
      <p className="mt-1.5 max-w-sm text-[13px] leading-relaxed text-text-muted">{message}</p>
      {detail && <p className="mt-2 text-[11px] text-text-faint">{detail}</p>}
      <div className="mt-4 flex gap-2"><Button variant="secondary" size="sm" onClick={onBack}>Go back</Button><Button size="sm" onClick={onReset}>Start over</Button></div>
    </div>
  )
}

function ReviewState({ detail, onReset, onConfirm, onBack }) {
  return (
    <div className="flex flex-col items-center text-center py-4">
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-warning-dim border border-warning/25">
        <AlertTriangle size={22} className="text-warning" />
      </div>
      <h3 className="text-[15px] font-medium text-text">Possible duplicate detected</h3>
      <p className="mt-1.5 max-w-sm text-[13px] leading-relaxed text-text-muted">
        This URL matches an existing resource variant. It will be saved as <span className="text-text">needs review</span> only if you explicitly confirm.
      </p>
      {detail && <p className="mt-2 max-w-sm break-all text-[11px] text-text-faint">{detail}</p>}
      <div className="mt-4 flex gap-2">
        <Button variant="secondary" size="sm" onClick={onBack}>Edit URL</Button>
        <Button size="sm" onClick={onConfirm}>Save as needs review</Button>
        <Button variant="ghost" size="sm" onClick={onReset}>Cancel</Button>
      </div>
    </div>
  )
}

function ErrorState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center text-center py-4">
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-danger-dim border border-danger/25"><XCircle size={22} className="text-danger" /></div>
      <h3 className="text-[15px] font-medium text-text">Couldn't save this resource</h3>
      <p className="mt-1.5 max-w-sm text-[13px] leading-relaxed text-text-muted">{message}</p>
      <Button variant="secondary" size="sm" className="mt-4" onClick={onRetry}>Try again</Button>
    </div>
  )
}
