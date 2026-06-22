import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/auth'
import { ToastProvider, Spinner } from './components/ui'
import Navbar from './components/layout/Navbar'
import HomePage from './pages/HomePage'
import { LoginPage, RegisterPage } from './pages/AuthPages'
import WatchPage from './pages/WatchPage'
import StudioPage from './pages/StudioPage'
import ProfilePage from './pages/ProfilePage'
import ChannelPage from './pages/ChannelPage'
import YandexCallback from './pages/YandexCallback'
import GoogleCallback from './pages/GoogleCallback'

function AppLayout() {
  const { user, loading, fetchMe } = useAuthStore()

  useEffect(() => { fetchMe() }, [])

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>▶</div>
          <Spinner size={28} />
        </div>
      </div>
    )
  }

  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/"                   element={<HomePage />} />
        <Route path="/login"              element={user ? <Navigate to="/" /> : <LoginPage />} />
        <Route path="/register"           element={user ? <Navigate to="/" /> : <RegisterPage />} />
        <Route path="/watch/:id"          element={<WatchPage />} />
        <Route path="/studio"             element={<StudioPage />} />
        <Route path="/profile"            element={<ProfilePage />} />
        <Route path="/profile/settings"   element={<ProfilePage />} />
        <Route path="/channel/:userId"    element={<ChannelPage />} />
        <Route path="/callback_yandex"    element={<YandexCallback />} />
        <Route path="/callback"    element={<GoogleCallback />} />
        <Route path="*"                   element={<NotFound />} />
      </Routes>
    </>
  )
}

function NotFound() {
  return (
    <div style={{ minHeight: '60vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1rem' }}>
      <div style={{ fontSize: '4rem' }}>404</div>
      <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem' }}>Page not found</h2>
      <a href="/" style={{ color: 'var(--accent)', fontSize: '.9375rem' }}>← Go home</a>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AppLayout />
      </ToastProvider>
    </BrowserRouter>
  )
}