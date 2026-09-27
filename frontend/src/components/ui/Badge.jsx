const TONES = {
  neutral: 'bg-elevated text-text-muted border-hairline-strong',
  accent: 'bg-accent-dim text-accent-soft border-accent/25',
  success: 'bg-success-dim text-success border-success/25',
  warning: 'bg-warning-dim text-warning border-warning/25',
  danger: 'bg-danger-dim text-danger border-danger/25',
}

export default function Badge({ tone = 'neutral', className = '', children }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[12px] font-medium leading-5 ${TONES[tone]} ${className}`}
    >
      {children}
    </span>
  )
}
