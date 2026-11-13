import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { AppShell } from './components'
import { LandingPage, LoginPage, DashboardPage, SchedulePage, OrdersPage, MachinesPage, DisruptionsPage, ReschedulingPage, ComparisonPage, AnalyticsPage, ReportsPage, SettingsPage } from './pages'

export default function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const [authenticated, setAuthenticated] = useState(() => localStorage.getItem('reschedule-auth') !== 'false')
  const login = () => { localStorage.setItem('reschedule-auth', 'true'); setAuthenticated(true); navigate('/dashboard') }
  if (!authenticated) return <Routes><Route path="/" element={<LandingPage />} /><Route path="/login" element={<LoginPage onLogin={login} />} /><Route path="*" element={<Navigate to="/" replace />} /></Routes>
  return <Routes><Route path="/" element={<LandingPage />} /><Route path="/login" element={<Navigate to="/dashboard" replace />} /><Route element={<AppShell />}><Route path="/dashboard" element={<DashboardPage />} /><Route path="/overview" element={<DashboardPage />} /><Route path="/schedule" element={<SchedulePage />} /><Route path="/orders" element={<OrdersPage />} /><Route path="/machines" element={<MachinesPage />} /><Route path="/disruptions" element={<DisruptionsPage />} /><Route path="/rescheduling" element={<ReschedulingPage />} /><Route path="/comparison" element={<ComparisonPage />} /><Route path="/analytics" element={<AnalyticsPage />} /><Route path="/reports" element={<ReportsPage />} /><Route path="/settings" element={<SettingsPage />} /></Route><Route path="*" element={<Navigate to="/" replace />} /></Routes>
}
