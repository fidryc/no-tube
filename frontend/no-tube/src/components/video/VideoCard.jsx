import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Badge, Avatar } from '../ui'

const VISIBILITY_LABELS = { PUBLIC: null, SUBSCRIPTION: 'Sub', PRIVATE: 'Private' }
const STATUS_LABELS    = { READY: null, DRAFT: 'Draft', PROCESSING: 'Processing', FAILED: 'Failed' }
const STATUS_COLORS    = { DRAFT: 'var(--text3)', PROCESSING: 'var(--yellow)', FAILED: 'var(--red)' }

export default function VideoCard({ video, showStatus = false }) {
  const nav = useNavigate()
  const [hov, setHov] = useState(false)
  const [authorHov, setAuthorHov] = useState(false)

  const visLabel = VISIBILITY_LABELS[video.visibility]
  const stLabel  = STATUS_LABELS[video.processing_status]
  const author   = video.user  // присутствует когда бэк возвращает VideoResponseWithUserSchema

  const goWatch   = e => { nav(`/watch/${video.id}`) }
  const goChannel = e => {
    e.stopPropagation()
    nav(`/channel/${video.user_id}`)
  }

  return (
    <div
      onClick={goWatch}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        cursor: 'pointer',
        background: 'var(--surface)',
        border: `1px solid ${hov ? 'var(--border2)' : 'var(--border)'}`,
        borderRadius: 'var(--radius2)',
        overflow: 'hidden',
        transition: 'all var(--transition)',
        transform: hov ? 'translateY(-3px)' : 'none',
        boxShadow: hov ? '0 12px 40px rgba(0,0,0,.4)' : 'none',
      }}
    >
      {/* Thumbnail */}
      <div style={{ width: '100%', aspectRatio: '16/9', background: 'var(--surface2)', position: 'relative', overflow: 'hidden' }}>
        {video.preview_url
          ? <img src={video.preview_url} alt={video.title} style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block', transform: hov ? 'scale(1.04)' : 'scale(1)', transition: 'transform .4s ease' }} />
          : <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text3)', fontSize: '2.5rem' }}>🎬</div>
        }
        {hov && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,.4)', animation: 'fadeIn .15s ease both' }}>
            <div style={{ width: 44, height: 44, borderRadius: '50%', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem', boxShadow: '0 4px 20px var(--accent-glow)' }}>▶</div>
          </div>
        )}
        <div style={{ position: 'absolute', top: '.5rem', right: '.5rem', display: 'flex', gap: '.35rem' }}>
          {visLabel && <Badge color="var(--accent)">{visLabel}</Badge>}
          {showStatus && stLabel && <Badge color={STATUS_COLORS[video.processing_status]}>{stLabel}</Badge>}
        </div>
      </div>

      {/* Info */}
      <div style={{ padding: '.75rem 1rem 1rem' }}>
        <h3 style={{
          fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '.9375rem',
          marginBottom: '.5rem', lineHeight: 1.35,
          display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden'
        }}>
          {video.title}
        </h3>

        {/* Author row — только если есть вложенный user */}
        {author && (
          <div
            onClick={goChannel}
            onMouseEnter={() => setAuthorHov(true)}
            onMouseLeave={() => setAuthorHov(false)}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: '.45rem',
              marginBottom: '.4rem', borderRadius: 20, padding: '.15rem .5rem .15rem .15rem',
              background: authorHov ? 'var(--surface2)' : 'transparent',
              transition: 'background var(--transition)',
            }}
          >
            <Avatar src={author.avatar_url} name={author.username} size={20} />
            <span style={{ fontSize: '.8rem', color: authorHov ? 'var(--text)' : 'var(--text2)', fontWeight: 500, transition: 'color var(--transition)' }}>
              {author.username}
            </span>
          </div>
        )}

        <p style={{ fontSize: '.8rem', color: 'var(--text3)' }}>
          {new Date(video.created_at).toLocaleDateString('ru', { day: 'numeric', month: 'short', year: 'numeric' })}
        </p>
      </div>
    </div>
  )
}
