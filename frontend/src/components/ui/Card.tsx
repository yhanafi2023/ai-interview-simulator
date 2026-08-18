import type { ComponentProps } from 'react'
import { cn } from '../../lib/cn'

export default function Card({ className, ...rest }: ComponentProps<'div'>) {
  return (
    <div
      className={cn('rounded-xl border border-slate-800 bg-slate-900 p-6', className)}
      {...rest}
    />
  )
}
