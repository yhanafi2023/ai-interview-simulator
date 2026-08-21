import { useMemo, useState, type ReactNode } from 'react'
import type { User } from '../../types'
import { AuthContext, type AuthState } from './auth-context'

export default function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)

  const value = useMemo<AuthState>(
    () => ({
      user,
      accessToken,
      signIn: (token, nextUser) => {
        setAccessToken(token)
        setUser(nextUser)
      },
      signOut: () => {
        setAccessToken(null)
        setUser(null)
      },
    }),
    [user, accessToken],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
