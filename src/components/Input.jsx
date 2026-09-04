export default function Input({ label, error, id, className = '', ...props }) {
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <label className="text-xs font-semibold text-slate-700" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        className={`w-full rounded-md border bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-orange-500 focus:ring-4 focus:ring-orange-100 ${
          error ? 'border-red-400' : 'border-slate-300'
        }`}
        {...props}
      />
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  )
}
