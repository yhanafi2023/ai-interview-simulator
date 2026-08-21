import Layout from './components/ui/Layout'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import KitchenSink from './pages/KitchenSink'
import Register from './pages/Register'
import { Routes, Route } from 'react-router'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="*" element={<h1>404 - Not Found</h1>} />
        <Route path="/kitchensink" element={<KitchenSink />} />
        <Route path="/register" element={<Register />} />
      </Route>
    </Routes>
  )
}
