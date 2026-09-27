export default function SegmentedControl({ options, value, onChange, className = '' }) {
  return (
    <div className={`inline-flex items-center rounded-lg border border-hairline-strong bg-elevated p-0.5 ${className}`}>
      {options.map((opt) => {
        const active = opt.value === value
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={`relative flex items-center gap-1.5 rounded-md px-3 h-7 text-[13px] font-medium transition-colors duration-150
              ${active ? 'bg-surface text-text shadow-[0_1px_2px_rgba(0,0,0,0.2)]' : 'text-text-muted hover:text-text'}`}
          >
            {opt.icon && <opt.icon size={14} />}
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}
