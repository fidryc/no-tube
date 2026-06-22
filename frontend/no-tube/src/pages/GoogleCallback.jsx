import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../api/client'
import { useAuthStore } from '../store/auth'
import { Spinner } from '../components/ui'

export default function GoogleCallback() {
  const nav = useNavigate()
  const { fetchMe } = useAuthStore()

  useEffect(() => {
    const params = new URLSearchParams(
      window.location.search
    )

    const code = params.get('code')

    if (!code) {
      nav('/login')
      return
    }

    authApi.googleCallback(code)
      .then(() => fetchMe())
      .then(() => nav('/'))
      .catch(() => nav('/login'))

  }, [])

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '1rem'
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 10,
          background: 'var(--accent)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        🔴
      </div>

      <Spinner size={28} />

      <p style={{
        color: 'var(--text2)',
        fontSize: '.875rem'
      }}>
        Signing you in via Google…
      </p>
    </div>
  )
}