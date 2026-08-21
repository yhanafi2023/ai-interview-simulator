import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router'
import { Link } from 'react-router'
import { z } from 'zod'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import { ApiRequestError, api } from '../lib/api'
import type { AuthResponse } from '../types'
import { useLocation } from 'react-router'
import { useAuth } from '../features/auth/auth-context'

const loginSchema = z.object({
  email: z.email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function Login() {
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })
  const { signIn } = useAuth()
  const location = useLocation()
  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname
  const mutation = useMutation({
    mutationFn: (values: LoginForm) => api.post<AuthResponse>('/auth/login', values),
    onSuccess: (data) => {
      signIn(data.accessToken, data.user)
      navigate(from ?? '/dashboard', { replace: true })
    },
  })

  return (
    <div className="mx-auto max-w-sm">
      <Card>
        <h1 className="text-2xl font-bold">Log in</h1>
        <p className="mt-1 text-sm text-slate-400">
          Any email works. Password is <code className="text-slate-300">password123</code>.
        </p>

        <form
          onSubmit={handleSubmit((values: LoginForm) => mutation.mutate(values))}
          className="mt-6 space-y-4"
          noValidate
        >
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
            autoComplete="current-password"
            error={errors.password?.message}
            {...register('password')}
          />

          {mutation.isError && (
            <p className="text-sm text-red-400">
              {mutation.error instanceof ApiRequestError
                ? mutation.error.detail
                : 'Something went wrong'}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={mutation.isPending}>
            {mutation.isPending ? 'Logging in…' : 'Log in'}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-400">
          Don't have an account?{' '}
          <Link to="/register" className="text-indigo-400 hover:text-indigo-300">
            Register
          </Link>
        </p>
      </Card>
    </div>
  )
}
