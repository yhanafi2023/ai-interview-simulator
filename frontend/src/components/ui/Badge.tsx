import type { ComponentProps } from 'react'
import { cn } from '../../lib/cn'

type Tone = 'neutral' | 'success' | 'warning' | 'danger' | 'info'

const toneStyles: Record<Tone, string> = {
  neutral: 'bg-slate-800 text-slate-300',
  success: 'bg-emerald-500/15 text-emerald-400',
  warning: 'bg-amber-500/15 text-amber-400',
  danger: 'bg-red-500/15 text-red-400',
  info: 'bg-indigo-500/15 text-indigo-300',
}

type BadgeProps = ComponentProps<'span'> & {
  tone?: Tone
}

export default function Badge({ tone = 'neutral', className, ...rest }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        toneStyles[tone],
        className,
      )}
      {...rest}
    />
  )
}
