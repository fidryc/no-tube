import { useState, useEffect, useCallback, createContext, useContext, useRef } from 'react'

/* ── Button ─────────────────────────────────────────────────────────────────── */
export function Btn({ children, variant = 'primary', size = 'md', loading, disabled, full, className = '', ...props }) {
  const base = {
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    gap: '.5rem', fontFamily: 'var(--font-body)', fontWeight: 500,
    borderRadius: 'var(--radius)', cursor: disabled || loading ? 'not-allowed' : 'pointer',
    transition: 'all var(--transition)', border: 'none', whiteSpace: 'nowrap',
    width: full ? '100%' : undefined,
    opacity: disabled || loading ? .55 : 1,
  }
  const sizes = {
    sm: { padding: '.35rem .75rem', fontSize: '.8125rem' },
    md: { padding: '.6rem 1.2rem', fontSize: '.9375rem' },
    lg: { padding: '.8rem 1.8rem', fontSize: '1rem' },
  }
  const variants = {
    primary: { background: 'var(--accent)', color: '#fff' },
    secondary: { background: 'var(--surface3)', color: 'var(--text)' },
    ghost: { background: 'transparent', color: 'var(--text2)', border: '1.5px solid var(--border)' },
    danger: { background: 'var(--red)', color: '#fff' },
    link: { background: 'transparent', color: 'var(--accent)', padding: 0 },
  }
  const hover = {
    primary: { filter: 'brightness(1.12)', boxShadow: '0 4px 20px var(--accent-glow)' },
    secondary: { background: 'var(--border)' },
    ghost: { borderColor: 'var(--accent)', color: 'var(--accent)' },
    danger: { filter: 'brightness(1.1)' },
    link: {},
  }
  const [hov, setHov] = useState(false)
  return (
    <button
      style={{ ...base, ...sizes[size], ...variants[variant], ...(hov && !disabled && !loading ? hover[variant] : {}) }}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      disabled={disabled || loading} {...props}
    >
      {loading && <Spinner size={14} color="currentColor" />}
      {children}
    </button>
  )
}

/* ── Input ──────────────────────────────────────────────────────────────────── */
export function Input({ label, error, hint, ...props }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '.35rem' }}>
      {label && <label style={{ fontSize: '.8125rem', color: 'var(--text2)', fontWeight: 500 }}>{label}</label>}
      <input style={{ borderColor: error ? 'var(--red)' : undefined }} {...props} />
      {error && <span style={{ fontSize: '.78rem', color: 'var(--red)' }}>{error}</span>}
      {hint && !error && <span style={{ fontSize: '.78rem', color: 'var(--text3)' }}>{hint}</span>}
    </div>
  )
}

export function Textarea({ label, error, ...props }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '.35rem' }}>
      {label && <label style={{ fontSize: '.8125rem', color: 'var(--text2)', fontWeight: 500 }}>{label}</label>}
      <textarea rows={4} style={{ resize: 'vertical', borderColor: error ? 'var(--red)' : undefined }} {...props} />
      {error && <span style={{ fontSize: '.78rem', color: 'var(--red)' }}>{error}</span>}
    </div>
  )
}

export function Select({ label, error, children, ...props }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '.35rem' }}>
      {label && <label style={{ fontSize: '.8125rem', color: 'var(--text2)', fontWeight: 500 }}>{label}</label>}
      <select {...props}>{children}</select>
      {error && <span style={{ fontSize: '.78rem', color: 'var(--red)' }}>{error}</span>}
    </div>
  )
}

/* ── Spinner ─────────────────────────────────────────────────────────────────── */
export function Spinner({ size = 24, color = 'var(--accent)' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      style={{ animation: 'spin .8s linear infinite', flexShrink: 0 }}>
      <circle cx="12" cy="12" r="10" stroke={color} strokeWidth="2.5" strokeOpacity=".2" />
      <path d="M12 2a10 10 0 0 1 10 10" stroke={color} strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}

/* ── Card ────────────────────────────────────────────────────────────────────── */
export function Card({ children, style, className, ...props }) {
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius2)',
      padding: '1.5rem',
      ...style
    }} {...props}>
      {children}
    </div>
  )
}

/* ── Modal ───────────────────────────────────────────────────────────────────── */
export function Modal({ open, onClose, title, children, width = 480 }) {
  useEffect(() => {
    if (!open) return
    const onKey = e => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null
  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,.7)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, backdropFilter: 'blur(4px)', padding: '1rem'
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        background: 'var(--surface)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius2)', padding: '2rem',
        width: '100%', maxWidth: width, maxHeight: '90vh', overflowY: 'auto',
        animation: 'fadeIn .2s ease both',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem' }}>{title}</h2>
          <button onClick={onClose} style={{
            background: 'var(--surface3)', border: 'none', borderRadius: '50%',
            width: 32, height: 32, color: 'var(--text2)', fontSize: '1.1rem',
            display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer'
          }}>✕</button>
        </div>
        {children}
      </div>
    </div>
  )
}

/* ── Toast ───────────────────────────────────────────────────────────────────── */
const ToastCtx = createContext(null)

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const id = useRef(0)

  const toast = useCallback((msg, type = 'info') => {
    const key = ++id.current
    setToasts(t => [...t, { key, msg, type }])
    setTimeout(() => setToasts(t => t.filter(x => x.key !== key)), 3500)
  }, [])

  const colors = { success: 'var(--green)', error: 'var(--red)', info: 'var(--accent)' }

  return (
    <ToastCtx.Provider value={toast}>
      {children}
      <div style={{ position: 'fixed', bottom: '1.5rem', right: '1.5rem', display: 'flex', flexDirection: 'column', gap: '.5rem', zIndex: 2000, maxWidth: 340 }}>
        {toasts.map(t => (
          <div key={t.key} style={{
            background: 'var(--surface)', border: `1px solid ${colors[t.type]}`,
            borderLeft: `4px solid ${colors[t.type]}`,
            borderRadius: 'var(--radius)', padding: '.8rem 1rem',
            fontSize: '.875rem', animation: 'fadeIn .25s ease both',
            boxShadow: '0 8px 32px rgba(0,0,0,.4)',
          }}>
            {t.msg}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  )
}

export function useToast() { return useContext(ToastCtx) }

/* ── Badge ───────────────────────────────────────────────────────────────────── */
export function Badge({ children, color = 'var(--accent)' }) {
  return (
    <span style={{
      background: `${color}22`, color, border: `1px solid ${color}44`,
      borderRadius: 6, padding: '.15rem .5rem', fontSize: '.75rem', fontWeight: 600, letterSpacing: '.02em'
    }}>
      {children}
    </span>
  )
}

/* ── Avatar ──────────────────────────────────────────────────────────────────── */
export function Avatar({ src, name = '?', size = 36 }) {
  const initials = name ? name.slice(0, 2).toUpperCase() : '?'
  if (src) return <img src={src} alt={name} style={{ width: size, height: size, borderRadius: '50%', objectFit: 'cover', flexShrink: 0 }} />
  return (
    <div style={{
      width: size, height: size, borderRadius: '50%', background: 'var(--accent)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: size * .35, fontWeight: 700, color: '#fff', flexShrink: 0,
      fontFamily: 'var(--font-display)',
    }}>
      {initials}
    </div>
  )
}

/* ── Empty state ─────────────────────────────────────────────────────────────── */
export function Empty({ icon = '📭', text = 'Nothing here yet' }) {
  return (
    <div style={{ textAlign: 'center', padding: '4rem 2rem', color: 'var(--text3)' }}>
      <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>{icon}</div>
      <p style={{ fontSize: '.9375rem' }}>{text}</p>
    </div>
  )
}

/* ── Section title ────────────────────────────────────────────────────────────── */
export function SectionTitle({ children, action }) {
  return (
    <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
      <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.35rem', fontWeight: 700 }}>{children}</h2>
      {action}
    </div>
  )
}

/* ── Tabs ────────────────────────────────────────────────────────────────────── */
export function Tabs({ tabs, active, onChange }) {
  return (
    <div style={{ display: 'flex', gap: '.25rem', background: 'var(--surface2)', borderRadius: 'var(--radius)', padding: '.25rem' }}>
      {tabs.map(t => (
        <button key={t.value} onClick={() => onChange(t.value)} style={{
          flex: 1, padding: '.45rem 1rem', borderRadius: 8, border: 'none',
          background: active === t.value ? 'var(--surface3)' : 'transparent',
          color: active === t.value ? 'var(--text)' : 'var(--text2)',
          fontWeight: active === t.value ? 600 : 400,
          fontSize: '.875rem', transition: 'all .15s', cursor: 'pointer',
          boxShadow: active === t.value ? '0 1px 4px rgba(0,0,0,.3)' : 'none',
        }}>
          {t.label}
        </button>
      ))}
    </div>
  )
}
