import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { videoApi, subApi, paymentApi } from '../api/client'
import VideoPlayer from '../components/video/VideoPlayer'
import { Btn, Spinner, Badge, useToast } from '../components/ui'
import { useAuthStore } from '../store/auth'

export default function WatchPage() {
  const { id } = useParams()
  const { user } = useAuthStore()
  const nav = useNavigate()
  const toast = useToast()

  const [video, setVideo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState(null)

  const [liked, setLiked] = useState(false)
  const [likeLoading, setLikeLoading] = useState(false)
  const [stats, setStats] = useState({ likes: 0, views: 0 })

  const [subInfo, setSubInfo] = useState(null)
  const [isSubscribed, setIsSubscribed] = useState(false)
  const [payLoading, setPayLoading] = useState(false)
  const [author, setAuthor] = useState(null)

  useEffect(() => {
    load()
  }, [id])

  const load = async () => {
    setLoading(true); setErr(null)
    try {
      const { data } = await videoApi.one(id)
      setVideo(data)
      fetchMeta(data)
    } catch (e) {
      setErr(e.friendlyMessage || 'Video not found')
    } finally { setLoading(false) }
  }

  const fetchMeta = async (v) => {
    // Author info
    try {
      const { default: ax } = await import('axios')
      const res = await ax.get(`/api/v1/user/${v.user_id}`, { withCredentials: true })
      setAuthor(res.data)
    } catch {}

    // Stats
    if (user) {
      try { const { data } = await videoApi.stats(id); setStats(data) } catch {}
      try { const { data } = await videoApi.isLiked(id); setLiked(data.liked) } catch {}
    }

    // Subscription info for subscription-gated videos
    if (v.visibility === 'SUBSCRIPTION') {
      try {
        const { data: subIdData } = await subApi.idByAuthor(v.user_id)
        if (subIdData.subscription_id) {
          const { data: sub } = await subApi.byId(subIdData.subscription_id)
          setSubInfo(sub.author_sub)
          if (user) {
            const { data: check } = await subApi.check(subIdData.subscription_id)
            setIsSubscribed(check.is_subscribed)
          }
        }
      } catch {}
    }
  }

  const toggleLike = async () => {
    if (!user) { nav('/login'); return }
    setLikeLoading(true)
    try {
      if (liked) {
        await videoApi.unlike(id)
        setLiked(false)
        setStats(s => ({ ...s, likes: s.likes - 1 }))
      } else {
        await videoApi.like(id)
        setLiked(true)
        setStats(s => ({ ...s, likes: s.likes + 1 }))
      }
    } catch (e) { toast(e.friendlyMessage || 'Error', 'error') }
    setLikeLoading(false)
  }

  const handlePay = async () => {
    if (!user) { nav('/login'); return }
    if (!subInfo) return
    setPayLoading(true)
    try {
      const { data } = await paymentApi.confirmationToken(subInfo.id)
      // Load YooKassa widget
      const script = document.createElement('script')
      script.src = 'https://yookassa.ru/checkout-widget/v1/checkout-widget.js'
      script.onload = () => {
        const checkout = new window.YooMoneyCheckoutWidget({
          confirmation_token: data.confirmation_token,
          return_url: window.location.href,
          error_callback: () => toast('Payment error', 'error'),
        })
        checkout.render('payment-widget')
      }
      document.body.appendChild(script)
    } catch (e) { toast(e.friendlyMessage || 'Payment error', 'error') }
    setPayLoading(false)
  }

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
      <Spinner size={48} />
    </div>
  )

  if (err) return (
    <div style={{ maxWidth: 600, margin: '5rem auto', textAlign: 'center', padding: '0 1.5rem' }}>
      <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔒</div>
      <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', marginBottom: '.5rem' }}>
        {err === 'Not found' ? 'Video not found' : err}
      </h2>
      <p style={{ color: 'var(--text2)', marginBottom: '1.5rem' }}>
        This video may be private, require a subscription, or not exist.
      </p>
      <Btn onClick={() => nav('/')}>Go home</Btn>
    </div>
  )

  const isSubGated = video.visibility === 'SUBSCRIPTION' && !isSubscribed && video.user_id !== user?.id

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '2rem 1.5rem' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '2rem', alignItems: 'start' }}>
        {/* Main */}
        <div style={{ minWidth: 0 }}>
          {/* Player or paywall */}
          {isSubGated ? (
            <PayWall sub={subInfo} onPay={handlePay} loading={payLoading} user={user} />
          ) : (
            <VideoPlayer videoId={id} />
          )}

          {/* Title + actions */}
          <div style={{ marginTop: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
              <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(1.1rem,3vw,1.5rem)', fontWeight: 700, lineHeight: 1.25 }}>
                {video.title}
              </h1>
              <div style={{ display: 'flex', gap: '.5rem', flexShrink: 0, alignItems: 'center' }}>
                <Badge color={video.visibility === 'PUBLIC' ? 'var(--green)' : video.visibility === 'SUBSCRIPTION' ? 'var(--accent)' : 'var(--text3)'}>
                  {video.visibility}
                </Badge>
              </div>
            </div>

            {/* Stats row */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '.75rem', flexWrap: 'wrap' }}>
              <span style={{ color: 'var(--text2)', fontSize: '.875rem' }}>
                {new Date(video.created_at).toLocaleDateString('ru', { day: 'numeric', month: 'long', year: 'numeric' })}
              </span>
              <span style={{ color: 'var(--text3)', fontSize: '.875rem' }}>👁 {stats.views}</span>
              <button onClick={toggleLike} disabled={likeLoading} style={{
                display: 'flex', alignItems: 'center', gap: '.4rem',
                background: liked ? 'rgba(124,92,252,.15)' : 'var(--surface2)',
                border: `1px solid ${liked ? 'var(--accent)' : 'var(--border)'}`,
                borderRadius: 20, padding: '.35rem .9rem', cursor: 'pointer',
                color: liked ? 'var(--accent)' : 'var(--text2)',
                fontSize: '.875rem', fontWeight: liked ? 600 : 400,
                transition: 'all var(--transition)',
              }}>
                {likeLoading ? <Spinner size={14} /> : '♥'} {stats.likes}
              </button>
            </div>

            {/* Description */}
            {video.description && (
              <div style={{
                marginTop: '1rem', padding: '1rem', background: 'var(--surface2)',
                borderRadius: 'var(--radius)', fontSize: '.9rem', color: 'var(--text2)', lineHeight: 1.65
              }}>
                {video.description}
              </div>
            )}
          </div>

          {/* YooKassa widget mount point */}
          <div id="payment-widget" style={{ marginTop: '1.5rem' }} />
        </div>

        {/* Sidebar: author */}
        <aside>
          {author && (
            <div style={{
              background: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius2)', padding: '1.5rem'
            }}>
              <AuthorCard author={author} subInfo={subInfo} isSubscribed={isSubscribed} onPay={handlePay} payLoading={payLoading} user={user} videoUserId={video.user_id} />
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}

function AuthorCard({ author, subInfo, isSubscribed, onPay, payLoading, user, videoUserId }) {
  const isOwn = user?.id === videoUserId
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '.75rem' }}>
        {author.avatar_url
          ? <img src={author.avatar_url} style={{ width: 48, height: 48, borderRadius: '50%', objectFit: 'cover' }} />
          : <div style={{ width: 48, height: 48, borderRadius: '50%', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.1rem' }}>{author.username.slice(0,2).toUpperCase()}</div>
        }
        <div>
          <div style={{ fontWeight: 600, fontFamily: 'var(--font-display)' }}>{author.username}</div>
          <div style={{ fontSize: '.8rem', color: 'var(--text3)' }}>Author</div>
        </div>
      </div>

      {subInfo && !isOwn && (
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
          <div style={{ fontSize: '.8125rem', color: 'var(--text2)', marginBottom: '.75rem' }}>
            🔐 Subscribe for exclusive content
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '.75rem', fontSize: '.875rem' }}>
            <span style={{ color: 'var(--text2)' }}>{subInfo.days} days</span>
            <span style={{ fontWeight: 700, color: 'var(--accent)' }}>{subInfo.price} ₽</span>
          </div>
          {isSubscribed
            ? <div style={{ textAlign: 'center', color: 'var(--green)', fontSize: '.875rem', fontWeight: 600 }}>✓ Subscribed</div>
            : <Btn full onClick={onPay} loading={payLoading}>Subscribe</Btn>
          }
        </div>
      )}
    </div>
  )
}

function PayWall({ sub, onPay, loading, user }) {
  const nav = useNavigate()
  return (
    <div style={{
      aspectRatio: '16/9', borderRadius: 'var(--radius2)',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      gap: '1rem', border: '1px solid var(--border)',
      background: 'radial-gradient(ellipse at center, rgba(124,92,252,.1) 0%, var(--surface2) 70%)'
    }}>
      <div style={{ fontSize: '3rem' }}>🔐</div>
      <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem' }}>Subscription required</h3>
      {sub && <p style={{ color: 'var(--text2)', fontSize: '.9rem' }}>
        {sub.days} days · <strong style={{ color: 'var(--accent)' }}>{sub.price} ₽</strong>
      </p>}
      <p style={{ color: 'var(--text3)', fontSize: '.8125rem', maxWidth: 300, textAlign: 'center' }}>
        This video is available to subscribers only
      </p>
      {user
        ? <Btn onClick={onPay} loading={loading} size="lg">Subscribe now</Btn>
        : <Btn onClick={() => nav('/login')} size="lg">Sign in to subscribe</Btn>
      }
    </div>
  )
}
