import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { useAuthStore } from '../store/auth'
import { authApi } from '../api/client'
import { Btn, Input, Card, SectionTitle, Avatar, useToast, Spinner } from '../components/ui'

export default function ProfilePage() {
  const { user, fetchMe, logout } = useAuthStore()
  const nav = useNavigate()
  const toast = useToast()
  const fileRef = useRef()

  const [avatarLoading, setAvatarLoading] = useState(false)
  const [pwForm, setPwForm] = useState({ old_password: '', new_password: '' })
  const [pwLoading, setPwLoading] = useState(false)

  if (!user) { nav('/login'); return null }

  const handleAvatarUpload = async e => {
    const file = e.target.files[0]
    if (!file) return
    setAvatarLoading(true)
    try {
      const { data } = await authApi.avatarUploadUrl()
      await axios.put(data.upload_url, file, { headers: { 'Content-Type': file.type } })
      await authApi.updateAvatar(data.key)
      await fetchMe()
      toast('Avatar updated!', 'success')
    } catch (e) { toast(e.friendlyMessage || 'Error uploading avatar', 'error') }
    setAvatarLoading(false)
  }

  const handlePwChange = async e => {
    e.preventDefault()
    setPwLoading(true)
    try {
      await authApi.changePassword({ old_password: pwForm.old_password, new_password: pwForm.new_password })
      toast('Password changed!', 'success')
      setPwForm({ old_password: '', new_password: '' })
    } catch (e) { toast(e.friendlyMessage || 'Error', 'error') }
    setPwLoading(false)
  }

  return (
    <div style={{ maxWidth: 700, margin: '0 auto', padding: '2rem 1.5rem' }}>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 800, marginBottom: '2rem' }}>Profile</h1>

      {/* Avatar + info */}
      <Card style={{ marginBottom: '1.5rem' }}>
        <SectionTitle>Identity</SectionTitle>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative' }}>
            {avatarLoading
              ? <div style={{ width: 72, height: 72, borderRadius: '50%', background: 'var(--surface2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Spinner size={24} /></div>
              : <Avatar src={user.avatar_url} name={user.username} size={72} />
            }
            <button onClick={() => fileRef.current.click()} style={{
              position: 'absolute', bottom: 0, right: 0, width: 24, height: 24,
              borderRadius: '50%', background: 'var(--accent)', border: '2px solid var(--bg)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer', fontSize: '.7rem', color: '#fff'
            }}>✏️</button>
            <input ref={fileRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={handleAvatarUpload} />
          </div>
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.1rem' }}>{user.username}</div>
            <div style={{ color: 'var(--text2)', fontSize: '.875rem' }}>{user.email}</div>
            <div style={{ display: 'flex', gap: '.5rem', marginTop: '.5rem', alignItems: 'center' }}>
              <span style={{
                fontSize: '.75rem', padding: '.15rem .5rem', borderRadius: 20,
                background: user.is_confirmed ? 'rgba(45,204,133,.15)' : 'rgba(245,200,66,.15)',
                color: user.is_confirmed ? 'var(--green)' : 'var(--yellow)',
                border: `1px solid ${user.is_confirmed ? 'rgba(45,204,133,.3)' : 'rgba(245,200,66,.3)'}`
              }}>
                {user.is_confirmed ? '✓ Verified' : '⚠ Unverified'}
              </span>
            </div>
          </div>
        </div>
      </Card>

      {/* Password change */}
      <Card style={{ marginBottom: '1.5rem' }}>
        <SectionTitle>Change password</SectionTitle>
        <form onSubmit={handlePwChange} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxWidth: 380 }}>
          <Input label="Current password" type="password" value={pwForm.old_password} onChange={e => setPwForm(f => ({ ...f, old_password: e.target.value }))} placeholder="••••••••" />
          <Input label="New password" type="password" value={pwForm.new_password} onChange={e => setPwForm(f => ({ ...f, new_password: e.target.value }))} placeholder="min 8 chars, 3 digits" hint="Min 8 chars, at least 3 digits and 1 letter" />
          <div>
            <Btn type="submit" loading={pwLoading}>Update password</Btn>
          </div>
        </form>
      </Card>

      {/* Account info */}
      <Card style={{ marginBottom: '1.5rem' }}>
        <SectionTitle>Account</SectionTitle>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '.5rem' }}>
          <InfoRow label="Member since" value={new Date(user.created_at).toLocaleDateString('ru', { day: 'numeric', month: 'long', year: 'numeric' })} />
          <InfoRow label="User ID" value={`#${user.id}`} />
        </div>
      </Card>

      {/* Danger zone */}
      <Card style={{ border: '1px solid rgba(255,77,106,.3)' }}>
        <SectionTitle>Session</SectionTitle>
        <Btn variant="danger" onClick={async () => { await logout(); nav('/') }}>Sign out</Btn>
      </Card>
    </div>
  )
}

function InfoRow({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '.5rem 0', borderBottom: '1px solid var(--border)' }}>
      <span style={{ color: 'var(--text2)', fontSize: '.875rem' }}>{label}</span>
      <span style={{ fontSize: '.875rem', fontWeight: 500 }}>{value}</span>
    </div>
  )
}
