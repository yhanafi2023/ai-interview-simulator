import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { api } from '../../lib/api'
import { setAccessToken } from '../../lib/auth-store'
import type { AuthResponse, User } from '../../types'
import { AuthContext, type AuthState } from './auth-context'

export default function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState<User | null>(null)
  const [isBootstrapping, setIsBootstrapping] = useState(true)

  useEffect(() => {
    let active = true

    api
      .post<AuthResponse>('/auth/refresh')
      .then((data) => {
        if (!active) return
        setAccessToken(data.accessToken)
        setUser(data.user)
      })
      .catch(() => {
        if (active) setAccessToken(null)
      })
      .finally(() => {
        if (active) setIsBootstrapping(false)
      })

    return () => {
      active = false
    }
  }, [])

  const value = useMemo<AuthState>(
    () => ({
      user,
      isBootstrapping,
      signIn: (token, nextUser) => {
        setAccessToken(token)
        setUser(nextUser)
      },
      signOut: () => {
        void api.post('/auth/logout').catch(() => undefined)
        setAccessToken(null)
        setUser(null)
        queryClient.clear()
      },
    }),
    [user, isBootstrapping, queryClient],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}