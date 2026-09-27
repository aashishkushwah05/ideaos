export default function StatCard({ icon: Icon, label, value, hint, tone = 'default' }) {
  const toneClass =
    tone === 'success'
      ? 'text-success'
      : tone === 'warning'
        ? 'text-warning'
        : tone === 'danger'
          ? 'text-danger'
          : 'text-accent-soft'

  return (
    <div className="rounded-xl border border-hairline bg-surface p-4">
      <div className="flex items-center justify-between">
        <span className="text-[13px] text-text-muted">{label}</span>
        {Icon && <Icon size={16} className={toneClass} />}
      </div>
      <div className="mt-2 font-display text-2xl font-semibold text-text tabular-nums">{value}</div>
      {hint && <div className="mt-1 text-[12px] text-text-faint">{hint}</div>}
    </div>
  )
}
