import { forwardRef } from 'react'

const VARIANTS = {
  primary:
    'bg-accent text-white hover:brightness-110 active:brightness-95 shadow-[0_1px_0_0_rgba(255,255,255,0.12)_inset]',
  secondary:
    'bg-elevated text-text border border-hairline-strong hover:border-accent/50 hover:bg-elevated/80',
  ghost:
    'bg-transparent text-text-muted hover:text-text hover:bg-elevated',
  danger:
    'bg-transparent text-danger border border-danger/30 hover:bg-danger-dim',
}

const SIZES = {
  sm: 'h-8 px-3 text-[13px] gap-1.5',
  md: 'h-9.5 px-4 text-sm gap-2',
  lg: 'h-11 px-5 text-[15px] gap-2',
}

const Button = forwardRef(function Button(
  { variant = 'primary', size = 'md', className = '', children, ...props },
  ref
) {
  return (
    <button
      ref={ref}
      className={`inline-flex items-center justify-center rounded-lg font-medium
        transition-all duration-150 ease-out
        disabled:opacity-40 disabled:pointer-events-none
        active:scale-[0.98]
        ${SIZES[size]} ${VARIANTS[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
})

export default Button
