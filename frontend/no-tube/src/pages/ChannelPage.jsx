import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { authApi, subApi, paymentApi, videoApi } from '../api/client'
import { useAuthStore } from '../store/auth'
import { Spinner, Empty, Avatar, Badge, Btn, useToast } from '../components/ui'
import VideoCard from '../components/video/VideoCard'

export default function ChannelPage() {
  const { userId } = useParams()
  const { user: me } = useAuthStore()
  const nav = useNavigate()
  const toast = useToast()

  const [author, setAuthor]           = useState(null)
  const [subPlan, setSubPlan]         = useState(null)   // AuthorSubscription
  const [isSubscribed, setIsSubscribed] = useState(false)
  const [subExpiresAt, setSubExpiresAt] = useState(null)
  const [videos, setVideos]           = useState([])
  const [subVideos, setSubVideos]     = useState([])     // subscription-only видео
  const [loading, setLoading]         = useState(true)
  const [payLoading, setPayLoading]   = useState(false)
  const [tab, setTab]                 = useState('all')  // 'all' | 'subscription'

  const isOwnChannel = me?.id === Number(userId)

  useEffect(() => { load() }, [userId, me])

  const load = async () => {
    setLoading(true)
    try {
      // Параллельно: автор + id плана подписки + публичные видео канала
      const [authorRes, subIdRes, videosRes] = await Promise.all([
        authApi.getUser(userId),
        subApi.idByAuthor(userId),
        videoApi.list({ user_id: userId }),
      ])

      setAuthor(authorRes.data)
      setVideos(videosRes.data)

      const subId = subIdRes.data.subscription_id
      if (subId) {
        // Параллельно: детали плана + статус подписки текущего юзера
        const [subRes, checkRes, subVideosRes] = await Promise.all([
          subApi.byId(subId),
          me ? subApi.check(subId) : Promise.resolve(null),
          subApi.byAuthor(userId),
        ])

        setSubPlan(subRes.data.author_sub)
        setSubVideos(subVideosRes.data)

        if (checkRes) {
          setIsSubscribed(checkRes.data.is_subscribed)
          // Дату истечения достаём из /me/subscriptions — там есть author_subscription_id
          // но не expires_at напрямую, поэтому пока показываем только булево
        }
      }
    } catch (e) {
      toast('Failed to load channel', 'error')
    }
    setLoading(false)
  }

  const handleSubscribe = async () => {
    if (!me) { nav('/login'); return }
    if (!subPlan) return
    setPayLoading(true)
    try {
      const { data } = await paymentApi.confirmationToken(subPlan.id)

      // Динамически грузим YooKassa виджет
      await loadYooKassaWidget(data.confirmation_token, () => {
        // После успешной оплаты webhook обновит подписку,
        // мы просто обновляем UI оптимистично
        setIsSubscribed(true)
        toast('Subscribed! Enjoy exclusive content.', 'success')
      })
    } catch (e) {
      toast(e.friendlyMessage || 'Payment error', 'error')
    }
    setPayLoading(false)
  }

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
      <Spinner size={40} />
    </div>
  )

  if (!author) return (
    <div style={{ textAlign: 'center', padding: '5rem', color: 'var(--text2)' }}>Channel not found</div>
  )

  const displayedVideos = tab === 'subscription' ? subVideos : videos

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '0 1.5rem 3rem' }}>

      {/* ── Banner + hero ─────────────────────────────────────────────────── */}
      <div style={{
        height: 180, borderRadius: '0 0 var(--radius2) var(--radius2)',
        background: 'linear-gradient(135deg, rgba(124,92,252,.3) 0%, rgba(160,127,255,.1) 100%)',
        marginBottom: '-60px', position: 'relative',
      }} />

      {/* ── Author card ────────────────────────────────────────────────────── */}
      <div style={{
        background: 'var(--surface)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius2)', padding: '1.5rem',
        display: 'flex', gap: '1.5rem', alignItems: 'flex-end',
        flexWrap: 'wrap', position: 'relative', zIndex: 1,
        marginBottom: '2rem',
      }}>
        {/* Avatar — чуть выходит за карточку */}
        <div style={{ marginTop: '-48px' }}>
          <div style={{ padding: 3, background: 'var(--surface)', borderRadius: '50%' }}>
            <Avatar src={author.avatar_url} name={author.username} size={80} />
          </div>
        </div>

        {/* Info */}
        <div style={{ flex: 1, minWidth: 200 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '.75rem', flexWrap: 'wrap' }}>
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', fontWeight: 800 }}>
              {author.username}
            </h1>
            {author.is_confirmed && (
              <Badge color="var(--green)">✓ Verified</Badge>
            )}
            {isOwnChannel && (
              <Badge color="var(--text3)">Your channel</Badge>
            )}
          </div>
          <p style={{ color: 'var(--text3)', fontSize: '.8125rem', marginTop: '.25rem' }}>
            Member since {new Date(author.created_at).toLocaleDateString('ru', { month: 'long', year: 'numeric' })}
          </p>
          <p style={{ color: 'var(--text2)', fontSize: '.875rem', marginTop: '.25rem' }}>
            {videos.length} public video{videos.length !== 1 ? 's' : ''}
            {subVideos.length > 0 && ` · ${subVideos.length} subscription`}
          </p>
        </div>

        {/* Subscription block */}
        {subPlan && !isOwnChannel && (
          <SubscriptionBlock
            plan={subPlan}
            isSubscribed={isSubscribed}
            onSubscribe={handleSubscribe}
            loading={payLoading}
          />
        )}

        {isOwnChannel && (
          <Btn variant="ghost" size="sm" onClick={() => nav('/studio')}>Manage Studio</Btn>
        )}
      </div>

      {/* YooKassa widget mount */}
      <div id="payment-widget" style={{ marginBottom: '1.5rem' }} />

      {/* ── Tabs ──────────────────────────────────────────────────────────── */}
      {subVideos.length > 0 && (
        <div style={{ display: 'flex', gap: '.25rem', background: 'var(--surface2)', borderRadius: 'var(--radius)', padding: '.25rem', marginBottom: '1.5rem', width: 'fit-content' }}>
          <TabBtn active={tab === 'all'} onClick={() => setTab('all')}>All videos</TabBtn>
          <TabBtn active={tab === 'subscription'} onClick={() => setTab('subscription')}>
            🔐 Subscription
          </TabBtn>
        </div>
      )}

      {/* ── Video grid ────────────────────────────────────────────────────── */}
      {tab === 'subscription' && !isSubscribed && !isOwnChannel && subPlan && (
        <SubscriptionGate plan={subPlan} onSubscribe={handleSubscribe} loading={payLoading} isLoggedIn={!!me} />
      )}

      {displayedVideos.length === 0 && (tab !== 'subscription' || isSubscribed || isOwnChannel)
        ? <Empty icon="🎬" text="No videos yet" />
        : (tab !== 'subscription' || isSubscribed || isOwnChannel) && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '1.25rem',
          }}>
            {displayedVideos.map((v, i) => (
              <div key={v.id} style={{ animationDelay: `${i * 0.04}s` }} className="animate-in">
                <VideoCard video={v} />
              </div>
            ))}
          </div>
        )
      }
    </div>
  )
}

/* ── Subscription block (в шапке канала) ────────────────────────────────────── */
function SubscriptionBlock({ plan, isSubscribed, onSubscribe, loading }) {
  return (
    <div style={{
      background: isSubscribed ? 'rgba(45,204,133,.08)' : 'rgba(124,92,252,.08)',
      border: `1px solid ${isSubscribed ? 'rgba(45,204,133,.25)' : 'rgba(124,92,252,.25)'}`,
      borderRadius: 'var(--radius)', padding: '1rem 1.25rem',
      minWidth: 200, textAlign: 'center',
    }}>
      {isSubscribed ? (
        <>
          <div style={{ color: 'var(--green)', fontWeight: 700, marginBottom: '.25rem' }}>✓ Subscribed</div>
          <div style={{ color: 'var(--text2)', fontSize: '.8125rem' }}>
            You have access to exclusive content
          </div>
        </>
      ) : (
        <>
          <div style={{ color: 'var(--text3)', fontSize: '.8rem', marginBottom: '.25rem' }}>Subscription</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '.4rem', justifyContent: 'center', marginBottom: '.75rem' }}>
            <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.4rem', color: 'var(--accent)' }}>
              {plan.price} ₽
            </span>
            <span style={{ color: 'var(--text3)', fontSize: '.8rem' }}>/ {plan.days} days</span>
          </div>
          <Btn onClick={onSubscribe} loading={loading} size="sm" full>
            Subscribe
          </Btn>
        </>
      )}
    </div>
  )
}

/* ── Paywall заглушка для вкладки Subscription ─────────────────────────────── */
function SubscriptionGate({ plan, onSubscribe, loading, isLoggedIn }) {
  const nav = useNavigate()
  return (
    <div style={{
      textAlign: 'center', padding: '4rem 2rem',
      background: 'radial-gradient(ellipse at center, rgba(124,92,252,.08) 0%, transparent 70%)',
      borderRadius: 'var(--radius2)', border: '1px solid var(--border)',
      marginBottom: '2rem',
    }}>
      <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔐</div>
      <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.35rem', marginBottom: '.5rem' }}>
        Exclusive content
      </h2>
      <p style={{ color: 'var(--text2)', marginBottom: '1.5rem', maxWidth: 380, margin: '0 auto 1.5rem' }}>
        Subscribe to unlock {plan.days}-day access to all premium videos on this channel.
      </p>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.75rem', color: 'var(--accent)' }}>
          {plan.price} ₽
        </span>
        {isLoggedIn
          ? <Btn onClick={onSubscribe} loading={loading} size="lg">Subscribe now</Btn>
          : <Btn onClick={() => nav('/login')} size="lg">Sign in to subscribe</Btn>
        }
      </div>
    </div>
  )
}

/* ── TabBtn ─────────────────────────────────────────────────────────────────── */
function TabBtn({ active, onClick, children }) {
  return (
    <button onClick={onClick} style={{
      padding: '.45rem 1rem', borderRadius: 8, border: 'none',
      background: active ? 'var(--surface3)' : 'transparent',
      color: active ? 'var(--text)' : 'var(--text2)',
      fontWeight: active ? 600 : 400,
      fontSize: '.875rem', cursor: 'pointer',
      transition: 'all .15s',
      boxShadow: active ? '0 1px 4px rgba(0,0,0,.3)' : 'none',
    }}>
      {children}
    </button>
  )
}

/* ── Helpers ────────────────────────────────────────────────────────────────── */
function loadYooKassaWidget(token, onSuccess) {
  return new Promise((resolve, reject) => {
    const existing = document.getElementById('yk-script')
    const mount = () => {
      try {
        const checkout = new window.YooMoneyCheckoutWidget({
          confirmation_token: token,
          return_url: window.location.href,
          error_callback: () => reject(new Error('Widget error')),
        })
        checkout.on('success', () => { onSuccess(); resolve() })
        checkout.render('payment-widget')
        resolve()
      } catch (e) { reject(e) }
    }
    if (window.YooMoneyCheckoutWidget) { mount(); return }
    const script = document.createElement('script')
    script.id = 'yk-script'
    script.src = 'https://yookassa.ru/checkout-widget/v1/checkout-widget.js'
    script.onload = mount
    script.onerror = reject
    document.body.appendChild(script)
  })
}
