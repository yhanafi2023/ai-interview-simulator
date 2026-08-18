import { useId, type ComponentProps } from 'react'
import { cn } from '../../lib/cn'

type InputProps = ComponentProps<'input'> & {
  label?: string
  error?: string
}

export default function Input({ label, error, className, id, ...rest }: InputProps) {
  const generatedId = useId()
  const inputId = id ?? generatedId
  const errorId = `${inputId}-error`
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-slate-300">
          {label}
        </label>
      )}
      <input
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          'w-full rounded-lg border bg-slate-950 px-3 py-2 text-sm text-slate-100',
          'placeholder:text-slate-500',
          'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-400',
          'disabled:opacity-50',
          error ? 'border-red-500' : 'border-slate-700',
          className,
        )}
        {...rest}
      />

      {error && (
        <p id={errorId} className="text-sm text-red-400">
          {error}
        </p>
      )}
    </div>
  )
}
