export default function Card({ as: Tag = 'div', className = '', interactive = false, children, ...props }) {
  return (
    <Tag
      className={`rounded-xl border border-hairline bg-surface
        ${interactive ? 'transition-all duration-200 ease-out hover:border-hairline-strong hover:bg-elevated/60 hover:-translate-y-0.5' : ''}
        ${className}`}
      {...props}
    >
      {children}
    </Tag>
  )
}
