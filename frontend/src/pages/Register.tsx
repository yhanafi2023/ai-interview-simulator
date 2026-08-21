import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router'
import { z } from 'zod'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import { ApiRequestError, api } from '../lib/api'
import type { AuthResponse } from '../types'

const registerSchema = z
  .object({
    displayName: z.string().min(1, 'Display name is required'),
    email: z.email('Enter a valid email address'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string(),
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

type RegisterForm = z.infer<typeof registerSchema>

export default function Register() {
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  })

  const mutation = useMutation({
    mutationFn: (values: RegisterForm) =>
      api.post<AuthResponse>('/auth/register', {
        email: values.email,
        password: values.password,
        displayName: values.displayName,
      }),
    onSuccess: () => navigate('/dashboard'),
  })

  return (
    <div className="mx-auto max-w-sm">
      <Card>
        <h1 className="text-2xl font-bold">Create an account</h1>
        <p className="mt-1 text-sm text-slate-400">
          Try <code className="text-slate-300">taken@example.com</code> to see the conflict error.
        </p>

        <form
          onSubmit={handleSubmit((values) => mutation.mutate(values))}
          className="mt-6 space-y-4"
          noValidate
        >
          <Input
            label="Display name"
            autoComplete="name"
            placeholder="Jack"
            error={errors.displayName?.message}
            {...register('displayName')}
          />

          <Input
            label="Email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            error={errors.email?.message}
            {...register('email')}
          />

          <Input
            label="Password"
            type="password"
            autoComplete="new-password"
            error={errors.password?.message}
            {...register('password')}
          />

          <Input
            label="Confirm password"
            type="password"
            autoComplete="new-password"
            error={errors.confirmPassword?.message}
            {...register('confirmPassword')}
          />

          {mutation.isError && (
            <p className="text-sm text-red-400">
              {mutation.error instanceof ApiRequestError
                ? mutation.error.detail
                : 'Something went wrong'}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={mutation.isPending}>
            {mutation.isPending ? 'Creating account…' : 'Create account'}
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-slate-400">
          Already have an account?{' '}
          <Link to="/login" className="text-indigo-400 hover:text-indigo-300">
            Log in
          </Link>
        </p>
      </Card>
    </div>
  )
}
