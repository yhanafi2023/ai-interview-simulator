import type { ComponentProps } from 'react'
import { cn } from '../../lib/cn'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
type Size = 'sm' | 'md' | 'lg'

type ButtonProps = ComponentProps<'button'> & {
  variant?: Variant
  size?: Size
}

const base =
  'inline-flex items-center justify-center rounded-lg font-medium transition-colors ' +
  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-400 ' +
  'disabled:pointer-events-none disabled:opacity-50'

const variantStyles: Record<Variant, string> = {
  primary: 'bg-indigo-600 text-white hover:bg-indigo-500',
  secondary: 'bg-slate-800 text-slate-100 hover:bg-slate-700',
  ghost: 'text-slate-300 hover:bg-slate-800 hover:text-white',
  danger: 'bg-red-600 text-white hover:bg-red-500',
}

const sizeStyles: Record<Size, string> = {
  sm: 'h-8 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  lg: 'h-12 px-6 text-base',
}

export default function Button({
  variant = 'primary',
  size = 'md',
  className,
  ...rest
}: ButtonProps) {
  return (
    <button className={cn(base, variantStyles[variant], sizeStyles[size], className)} {...rest} />
  )
}
