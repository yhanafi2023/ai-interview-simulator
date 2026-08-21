import { NavLink } from 'react-router'
import { useAuth } from '../../features/auth/auth-context'
import Button from '../ui/Button'

const publicLinks = [{ to: '/', label: 'Home' }]
const privateLinks = [{ to: '/dashboard', label: 'Dashboard' }]

export default function NavBar() {
  const { user, signOut } = useAuth()
  const links = user ? [...publicLinks, ...privateLinks] : publicLinks

  return (
    <header className="border-b border-slate-800">
      <nav className="mx-auto flex max-w-5xl items-center gap-8 px-6 py-4">
        <span className="font-bold">InterviewAI</span>

        <div className="flex gap-5 text-sm">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/'}
              className={({ isActive }) =>
                isActive ? 'text-white' : 'text-slate-400 hover:text-slate-200'
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-3 text-sm">
          {user ? (
            <>
              <span className="text-slate-400">{user.displayName}</span>
              <Button size="sm" variant="ghost" onClick={signOut}>
                Log out
              </Button>
            </>
          ) : (
            <NavLink to="/login" className="text-slate-400 hover:text-slate-200">
              Log in
            </NavLink>
          )}
        </div>
      </nav>
    </header>
  )
}
