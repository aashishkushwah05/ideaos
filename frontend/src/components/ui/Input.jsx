import { forwardRef } from 'react'

export const Input = forwardRef(function Input(
  { icon: Icon, error, className = '', ...props },
  ref
) {
  return (
    <div className="relative">
      {Icon && (
        <Icon
          size={16}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-faint"
        />
      )}
      <input
        ref={ref}
        className={`w-full rounded-lg border bg-elevated text-[14px] text-text placeholder:text-text-faint
          h-9.5 outline-none transition-colors duration-150
          ${Icon ? 'pl-9 pr-3' : 'px-3'}
          ${error ? 'border-danger/50 focus:border-danger' : 'border-hairline-strong focus:border-accent'}
          ${className}`}
        {...props}
      />
    </div>
  )
})

export const Textarea = forwardRef(function Textarea({ error, className = '', ...props }, ref) {
  return (
    <textarea
      ref={ref}
      className={`w-full rounded-lg border bg-elevated text-[14px] text-text placeholder:text-text-faint
        px-3 py-2.5 outline-none transition-colors duration-150 resize-none
        ${error ? 'border-danger/50 focus:border-danger' : 'border-hairline-strong focus:border-accent'}
        ${className}`}
      {...props}
    />
  )
})
