export default function Button({
  children,
  variant = 'primary',
  className = '',
  type = 'button',
  ...props
}) {
  const variants = {
    primary:
      'bg-orange-500 text-white shadow-sm hover:bg-orange-600 focus-visible:ring-orange-200',
    secondary:
      'border border-slate-300 bg-white text-slate-700 hover:border-slate-400 hover:bg-slate-50 focus-visible:ring-slate-200',
  }

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-4 disabled:cursor-not-allowed disabled:opacity-60 ${variants[variant] || variants.primary} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
