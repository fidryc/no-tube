import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/auth'
import { Avatar, Btn } from '../ui'

export default function Navbar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    navigate('/')
    setMenuOpen(false)
  }

  return (
    <header style={{
      position: 'sticky', top: 0, zIndex: 100,
      borderBottom: '1px solid var(--border)',
      background: 'rgba(10,10,15,.9)', backdropFilter: 'blur(16px)',
    }}>
      <div style={{
        maxWidth: 1280, margin: '0 auto', padding: '0 1.5rem',
        height: 60, display: 'flex', alignItems: 'center', gap: '1.5rem'
      }}>
        {/* Logo */}
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '.5rem', flexShrink: 0 }}>
          <div style={{
            width: 30, height: 30, borderRadius: 8, background: 'var(--accent)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem'
          }}>▶</div>
          <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.1rem', letterSpacing: '-.02em' }}>
            NoTube
          </span>
        </Link>

        {/* Search */}
        <div style={{ flex: 1, maxWidth: 480 }}>
          <form onSubmit={e => { e.preventDefault(); const q = e.target.q.value.trim(); if (q) navigate(`/?q=${encodeURIComponent(q)}`) }}>
            <input name="q" placeholder="Search videos…" defaultValue={new URLSearchParams(location.search).get('q') || ''} style={{ height: 36, fontSize: '.875rem' }} />
          </form>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '.75rem', marginLeft: 'auto' }}>
          {user ? (
            <>
              <Btn size="sm" variant="secondary" onClick={() => navigate('/studio')}>Studio</Btn>
              <div style={{ position: 'relative' }}>
                <button onClick={() => setMenuOpen(v => !v)} style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: '.5rem', padding: '.25rem',
                  borderRadius: 'var(--radius)'
                }}>
                  <Avatar src={user.avatar_url} name={user.username} size={32} />
                  <span style={{ fontSize: '.875rem', color: 'var(--text2)', display: 'none' }}>{user.username}</span>
                </button>
                {menuOpen && (
                  <div onClick={() => setMenuOpen(false)} style={{
                    position: 'absolute', right: 0, top: 'calc(100% + .5rem)',
                    background: 'var(--surface)', border: '1px solid var(--border)',
                    borderRadius: 'var(--radius)', padding: '.5rem', minWidth: 180,
                    boxShadow: '0 16px 40px rgba(0,0,0,.5)', animation: 'fadeIn .15s ease both', zIndex: 200
                  }}>
                    <MenuItem to="/profile">Profile</MenuItem>
                    <MenuItem to="/studio">Studio</MenuItem>
                    <MenuItem to="/profile/settings">Settings</MenuItem>
                    <div style={{ height: 1, background: 'var(--border)', margin: '.4rem 0' }} />
                    <button onClick={handleLogout} style={{
                      width: '100%', textAlign: 'left', padding: '.5rem .75rem',
                      background: 'none', border: 'none', color: 'var(--red)',
                      borderRadius: 6, fontSize: '.875rem', cursor: 'pointer'
                    }}>Sign out</button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <Btn size="sm" variant="ghost" onClick={() => navigate('/login')}>Sign in</Btn>
              <Btn size="sm" onClick={() => navigate('/register')}>Sign up</Btn>
            </>
          )}
        </div>
      </div>
    </header>
  )
}

function MenuItem({ to, children }) {
  return (
    <Link to={to} style={{
      display: 'block', padding: '.5rem .75rem', borderRadius: 6,
      fontSize: '.875rem', color: 'var(--text)',
      transition: 'background .15s',
    }}
      onMouseEnter={e => e.target.style.background = 'var(--surface2)'}
      onMouseLeave={e => e.target.style.background = 'none'}
    >
      {children}
    </Link>
  )
}
