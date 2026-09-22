import { Navigate, Outlet, useLocation } from 'react-router'
import { useAuth } from './auth-context'

export default function ProtectedRoute() {
  const { user, isBootstrapping } = useAuth()
  const location = useLocation()

  if (isBootstrapping) {
    return <p className="text-slate-400">Loading…</p>
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <Outlet />
}