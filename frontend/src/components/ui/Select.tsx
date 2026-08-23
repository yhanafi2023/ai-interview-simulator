import { useId, type ComponentProps } from 'react'
import { cn } from '../../lib/cn'

type SelectProps = ComponentProps<'select'> & {
  label?: string
}

export default function Select({ label, className, id, ...rest }: SelectProps) {
  const generatedId = useId()
  const selectId = id ?? generatedId

  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={selectId} className="block text-sm font-medium text-slate-300">
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={cn(
          'w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100',
          'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-400',
          className,
        )}
        {...rest}
      />
    </div>
  )
}
