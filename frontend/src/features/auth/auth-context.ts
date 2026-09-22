import { createContext, useContext } from 'react'
import type { User } from '../../types'

export type AuthState = {
  user: User | null
  isBootstrapping: boolean
  signIn: (token: string, user: User) => void
  signOut: () => void
}

export const AuthContext = createContext<AuthState | null>(null)

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used inside an AuthProvider')
  }
  return ctx
}
