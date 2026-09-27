import { X, ChevronDown } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'

function FilterDropdown({ label, options, value, onChange }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    function onClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  const active = value !== 'all'

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={`inline-flex h-8 items-center gap-1.5 rounded-lg border px-3 text-[13px] font-medium transition-colors duration-150
          ${active ? 'border-accent/40 bg-accent-dim text-accent-soft' : 'border-hairline-strong bg-elevated text-text-muted hover:text-text'}`}
      >
        {label}
        <ChevronDown size={13} className={`transition-transform duration-150 ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="absolute left-0 top-full z-20 mt-1.5 min-w-[170px] overflow-hidden rounded-lg border border-hairline-strong bg-surface p-1 shadow-[0_8px_24px_rgba(0,0,0,0.35)] animate-[fadeIn_0.12s_ease-out]">
          {options.map((opt) => (
            <button
              key={opt.value}
              onClick={() => {
                onChange(opt.value)
                setOpen(false)
              }}
              className={`flex w-full items-center justify-between rounded-md px-2.5 py-1.5 text-left text-[13px] transition-colors duration-100
                ${value === opt.value ? 'bg-accent-dim text-accent-soft' : 'text-text-muted hover:bg-elevated hover:text-text'}`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function FilterBar({ filters, values, onChange, onClear }) {
  const activeCount = filters.filter((f) => values[f.key] !== 'all').length

  return (
    <div className="flex flex-wrap items-center gap-2">
      {filters.map((f) => (
        <FilterDropdown
          key={f.key}
          label={f.label}
          options={f.options}
          value={values[f.key]}
          onChange={(v) => onChange(f.key, v)}
        />
      ))}
      {activeCount > 0 && (
        <button
          type="button"
          onClick={onClear}
          className="inline-flex h-8 items-center gap-1 rounded-lg px-2.5 text-[13px] text-text-faint transition-colors duration-150 hover:text-danger"
        >
          <X size={13} />
          Clear
        </button>
      )}
    </div>
  )
}
