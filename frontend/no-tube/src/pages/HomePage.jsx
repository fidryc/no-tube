import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { videoApi } from '../api/client'
import VideoCard from '../components/video/VideoCard'
import { Spinner, Empty } from '../components/ui'

const LIMIT = 16

export default function HomePage() {
  const [searchParams] = useSearchParams()
  const q = searchParams.get('q') || ''

  const [videos, setVideos] = useState([])
  const [loading, setLoading] = useState(true)
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)

  // Начальная загрузка — сбрасывается при смене q
  useEffect(() => {
    let cancelled = false

    setVideos([])
    setOffset(0)
    setHasMore(true)
    setLoading(true)

    const fetch = async () => {
      try {
        const params = { limit: LIMIT, offset: 0 }
        if (q) params.title = q
        const { data } = await videoApi.list(params)
        if (cancelled) return
        setVideos(data)
        setHasMore(data.length === LIMIT)
        setOffset(data.length)
      } catch {}
      if (!cancelled) setLoading(false)
    }

    fetch()
    return () => { cancelled = true }
  }, [q])

  // Подгрузка следующей страницы
  const loadMore = async () => {
    if (loadingMore) return
    setLoadingMore(true)
    try {
      const params = { limit: LIMIT, offset }
      if (q) params.title = q
      const { data } = await videoApi.list(params)
      setVideos(prev => [...prev, ...data])
      setHasMore(data.length === LIMIT)
      setOffset(prev => prev + data.length)
    } catch {}
    setLoadingMore(false)
  }

  return (
    <main style={{ maxWidth: 1280, margin: '0 auto', padding: '2rem 1.5rem' }}>
      <div style={{
        textAlign: 'center', marginBottom: '3rem',
        padding: '3rem 1rem 2rem',
        background: 'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(124,92,252,.12) 0%, transparent 70%)',
        borderRadius: 'var(--radius3)',
      }}>
        <h1 style={{
          fontFamily: 'var(--font-display)', fontSize: 'clamp(2rem,5vw,3.5rem)',
          fontWeight: 800, lineHeight: 1.1, marginBottom: '.75rem',
          background: 'linear-gradient(135deg, #fff 0%, var(--accent2) 100%)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'
        }}>
          {q ? `Results for "${q}"` : 'Discover videos'}
        </h1>
        <p style={{ color: 'var(--text2)', fontSize: '1.0625rem' }}>
          {q ? 'Showing matching content' : 'Public content from creators around the world'}
        </p>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
          <Spinner size={40} />
        </div>
      ) : videos.length === 0 ? (
        <Empty icon="🎬" text={q ? 'No videos found for this search' : 'No videos published yet'} />
      ) : (
        <>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '1.25rem'
          }}>
            {videos.map((v, i) => (
              <div key={v.id} style={{ animationDelay: `${(i % LIMIT) * 0.04}s` }} className="animate-in">
                <VideoCard video={v} />
              </div>
            ))}
          </div>

          {hasMore && (
            <div style={{ textAlign: 'center', marginTop: '2.5rem' }}>
              <button onClick={loadMore} disabled={loadingMore} style={{
                background: 'var(--surface2)', border: '1px solid var(--border)',
                borderRadius: 'var(--radius)', padding: '.7rem 2rem',
                color: 'var(--text)', cursor: loadingMore ? 'not-allowed' : 'pointer',
                fontSize: '.9375rem', display: 'inline-flex', alignItems: 'center', gap: '.5rem',
                transition: 'all var(--transition)', opacity: loadingMore ? .6 : 1,
              }}>
                {loadingMore && <Spinner size={16} />}
                Load more
              </button>
            </div>
          )}
        </>
      )}
    </main>
  )
}