import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { Btn, Input, Card, useToast } from '../components/ui'
import { authApi } from '../api/client'

const Divider = () => (
  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', color: 'var(--text3)', fontSize: '.8125rem' }}>
    <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
    or
    <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
  </div>
)

/* ── OAuth buttons ──────────────────────────────────────────────────────────── */
function OAuthButtons({ mode }) {
  const { fetchMe } = useAuthStore()
  const toast = useToast()

  const handleYandex = async () => {
    try {
      const { data } = await authApi.yandexParams()
      const url = `https://oauth.yandex.ru/authorize?response_type=${data.response_type}&client_id=${data.client_id}&redirect_uri=${encodeURIComponent(data.redirect_uri)}`
      window.location.href = url
    } catch { toast('Could not connect to Yandex', 'error') }
  }

  const handleGoogle = async () => {
    try {
      // const { data } = await authApi.googleUrl()
      window.location.href = '/api/v1/user/google/url'
    } catch { toast('Could not connect to Google', 'error') }
  }
  const GoogleIcon = () => (
  <svg width="20" height="20" viewBox="0 0 48 48">
    <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.9 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.1 8 3l5.7-5.7C34.5 6.5 29.6 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20c11 0 19.5-8 19.5-20 0-1.3-.1-2.7-.4-3.5z"/>
    <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.5 16 18.9 13 24 13c3.1 0 5.8 1.1 8 3l5.7-5.7C34.5 6.5 29.6 4 24 4c-7.7 0-14.3 4.4-17.7 10.7z"/>
    <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.5 26.7 36 24 36c-5.3 0-9.7-3.1-11.3-7.6l-6.6 5.1C9.5 39.6 16.2 44 24 44z"/>
    <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.9 2.5-2.5 4.6-4.6 6.1l6.2 5.2C40.9 36.1 44 30.6 44 24c0-1.3-.1-2.7-.4-3.5z"/>
  </svg>
);

const YandexIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="12" fill="#FC3F1D"/>
    <path fill="#fff" d="M13.5 6.5h-1.8c-2 0-3.6 1.6-3.6 3.6 0 1.5.8 2.4 2 3l-2.3 4.4h2l2-4h1v4h1.7V6.5zm-1.7 5.2h-.2c-1 0-1.7-.6-1.7-1.6s.7-1.6 1.7-1.6h.2v3.2z"/>
  </svg>
);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '.6rem' }}>
      <OAuthBtn icon={<GoogleIcon />} label="Continue with Google" onClick={handleGoogle} />
      <OAuthBtn icon={<YandexIcon />} label="Continue with Yandex" onClick={handleYandex} />
    </div>
  )
}

function OAuthBtn({ icon, label, onClick }) {
  const [hov, setHov] = useState(false)
  return (
    <button onClick={onClick} onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)} style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '.6rem',
      width: '100%', padding: '.6rem', borderRadius: 'var(--radius)',
      background: hov ? 'var(--surface3)' : 'var(--surface2)',
      border: '1.5px solid var(--border)', color: 'var(--text)',
      fontSize: '.9375rem', fontFamily: 'var(--font-body)', cursor: 'pointer',
      transition: 'all var(--transition)',
    }}>
      <span>{icon}</span> {label}
    </button>
  )
}

/* ── Login Page ──────────────────────────────────────────────────────────────── */
export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')
  const { login } = useAuthStore()
  const nav = useNavigate()
  const toast = useToast()

  const submit = async e => {
    e.preventDefault()
    setErr('')
    setLoading(true)
    try {
      await login(email, password)
      toast('Welcome back!', 'success')
      nav('/')
    } catch (e) {
      setErr(e.friendlyMessage || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return <AuthLayout title="Sign in" subtitle="Good to see you again">
    <OAuthButtons mode="login" />
    <Divider />
    <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <Input label="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required />
      <Input label="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required />
      {err && <ErrBox msg={err} />}
      <Btn type="submit" loading={loading} full>Sign in</Btn>
    </form>
    <p style={{ textAlign: 'center', fontSize: '.8125rem', color: 'var(--text2)' }}>
      No account? <Link to="/register" style={{ color: 'var(--accent)' }}>Sign up</Link>
    </p>
  </AuthLayout>
}

/* ── Register Page ────────────────────────────────────────────────────────────── */
export function RegisterPage() {
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [errs, setErrs] = useState({})
  const { register } = useAuthStore()
  const nav = useNavigate()
  const toast = useToast()

  const set = key => e => setForm(f => ({ ...f, [key]: e.target.value }))

  const submit = async e => {
    e.preventDefault()
    setErrs({})
    setLoading(true)
    try {
      await register(form.username, form.email, form.password)
      toast('Account created! Check your email to confirm.', 'success')
      nav('/')
    } catch (e) {
      if (e.errorCode === 'VALIDATION_ERROR') {
        const map = {}
        e.response?.data?.error?.details?.forEach(d => { map[d.field] = d.message })
        setErrs(map)
      } else {
        setErrs({ _: e.friendlyMessage || 'Registration failed' })
      }
    } finally { setLoading(false) }
  }

  return <AuthLayout title="Create account" subtitle="Join NoTube today">
    <OAuthButtons mode="register" />
    <Divider />
    <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <Input label="Username" value={form.username} onChange={set('username')} placeholder="at least 8 characters" error={errs.username} required />
      <Input label="Email" type="email" value={form.email} onChange={set('email')} placeholder="you@example.com" error={errs.email} required />
      <Input label="Password" type="password" value={form.password} onChange={set('password')} placeholder="min 8 chars, 3 digits" error={errs.password} hint="Min 8 chars, at least 3 digits and 1 letter" required />
      {errs._ && <ErrBox msg={errs._} />}
      <Btn type="submit" loading={loading} full>Create account</Btn>
    </form>
    <p style={{ textAlign: 'center', fontSize: '.8125rem', color: 'var(--text2)' }}>
      Already have an account? <Link to="/login" style={{ color: 'var(--accent)' }}>Sign in</Link>
    </p>
  </AuthLayout>
}

/* ── Shared layout ───────────────────────────────────────────────────────────── */
function AuthLayout({ title, subtitle, children }) {
  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '1.5rem',
      background: 'radial-gradient(ellipse 60% 60% at 50% 0%, rgba(124,92,252,.15) 0%, transparent 70%)',
    }}>
      <div style={{ width: '100%', maxWidth: 420, animation: 'fadeIn .3s ease both' }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '.5rem', justifyContent: 'center', marginBottom: '2rem' }}>
          <div style={{ width: 36, height: 36, borderRadius: 10, background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem' }}>▶</div>
          <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.25rem' }}>NoTube</span>
        </Link>
        <Card>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', fontWeight: 800, marginBottom: '.25rem' }}>{title}</h1>
          <p style={{ color: 'var(--text2)', fontSize: '.875rem', marginBottom: '1.5rem' }}>{subtitle}</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {children}
          </div>
        </Card>
      </div>
    </div>
  )
}

function ErrBox({ msg }) {
  return (
    <div style={{ background: 'rgba(255,77,106,.1)', border: '1px solid rgba(255,77,106,.3)', borderRadius: 'var(--radius)', padding: '.65rem 1rem', fontSize: '.875rem', color: 'var(--red)' }}>
      {msg}
    </div>
  )
}
