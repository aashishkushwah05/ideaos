export function SkeletonLine({ className = '' }) {
  return <div className={`skeleton rounded-md ${className}`} />
}

export function SkeletonCard() {
  return (
    <div className="rounded-xl border border-hairline bg-surface p-4 space-y-3">
      <div className="flex items-center gap-2">
        <SkeletonLine className="h-7 w-7 rounded-full" />
        <SkeletonLine className="h-3 w-20" />
      </div>
      <SkeletonLine className="h-4 w-4/5" />
      <SkeletonLine className="h-3 w-full" />
      <SkeletonLine className="h-3 w-2/3" />
      <div className="flex gap-2 pt-1">
        <SkeletonLine className="h-5 w-14 rounded-full" />
        <SkeletonLine className="h-5 w-16 rounded-full" />
      </div>
    </div>
  )
}

export function SkeletonRow() {
  return (
    <div className="flex items-center gap-4 rounded-lg border border-hairline bg-surface px-4 py-3">
      <SkeletonLine className="h-8 w-8 rounded-md shrink-0" />
      <div className="flex-1 space-y-2">
        <SkeletonLine className="h-3.5 w-2/5" />
        <SkeletonLine className="h-3 w-3/5" />
      </div>
      <SkeletonLine className="h-5 w-16 rounded-full hidden sm:block" />
      <SkeletonLine className="h-3 w-14 hidden md:block" />
    </div>
  )
}
