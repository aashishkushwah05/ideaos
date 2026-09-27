export const STATUS_META = {
  unique: { label: 'Saved', tone: 'success' },
  needs_review: { label: 'Needs review', tone: 'warning' },
  possible_duplicate: { label: 'Possible duplicate', tone: 'warning' },
  exact_duplicate: { label: 'Duplicate', tone: 'neutral' },
  invalid: { label: 'Invalid URL', tone: 'danger' },
}

export function statusMeta(status) {
  return STATUS_META[status] || STATUS_META.unique
}
