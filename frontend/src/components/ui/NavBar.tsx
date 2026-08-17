import { NavLink } from 'react-router'

const links = [
  { to: '/', label: 'Home' },
  { to: '/login', label: 'Login' },
  { to: '/dashboard', label: 'Dashboard' },
]
export default function NavBar() {
  return (
    <header className="border-b border-slate-800">
      <nav className="mx-auto flex max-w-5xl items-center gap-8 px-6 py-4">
        <span className="fond-bold">InterviewAI</span>
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
      </nav>
    </header>
  )
}
