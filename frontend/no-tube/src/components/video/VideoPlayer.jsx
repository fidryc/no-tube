import { useEffect, useRef, useState } from 'react'
import { videoApi } from '../../api/client'
import { Spinner } from '../ui'

export default function VideoPlayer({ videoId }) {
  const videoRef = useRef(null)
  const playerRef = useRef(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!videoId) return
    let destroyed = false

    const initPlayer = async () => {
      try {
        // fetch manifest (the server returns the mpd xml directly)
        const res = await videoApi.dash(videoId)
        if (destroyed) return

        const blob = new Blob([res.data], { type: 'application/dash+xml' })
        const blobUrl = URL.createObjectURL(blob)

        // dynamic import dash.js
        const dashjs = await import('dashjs')
        if (destroyed) { URL.revokeObjectURL(blobUrl); return }

        const player = dashjs.MediaPlayer().create()
        playerRef.current = player

        player.initialize(videoRef.current, blobUrl, false)
        player.updateSettings({
          streaming: {
            abr: { autoSwitchBitrate: { video: true } },
            request: {
              withCredentials: true
            }
          }
        })

        player.on(dashjs.MediaPlayer.events.CAN_PLAY, () => setLoading(false))
        player.on(dashjs.MediaPlayer.events.ERROR, () => {
          setError('Playback error')
          setLoading(false)
        })
      } catch (e) {
        if (!destroyed) {
          setError(e.friendlyMessage || 'Could not load video')
          setLoading(false)
        }
      }
    }

    initPlayer()

    return () => {
      destroyed = true
      if (playerRef.current) {
        try { playerRef.current.destroy() } catch {}
        playerRef.current = null
      }
    }
  }, [videoId])

  // record watch event once
  useEffect(() => {
    if (!videoId) return
    const t = setTimeout(() => {
      videoApi.watch(videoId).catch(() => {})
    }, 5000)
    return () => clearTimeout(t)
  }, [videoId])

  return (
    <div style={{ position: 'relative', width: '100%', aspectRatio: '16/9', background: '#000', borderRadius: 'var(--radius2)', overflow: 'hidden' }}>
      {loading && (
        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,.7)', zIndex: 2 }}>
          <Spinner size={40} />
        </div>
      )}
      {error && (
        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text2)', gap: '.75rem', background: '#000' }}>
          <span style={{ fontSize: '2rem' }}>⚠️</span>
          <span style={{ fontSize: '.9375rem' }}>{error}</span>
        </div>
      )}
      <video
        ref={videoRef}
        controls
        style={{ width: '100%', height: '100%', display: 'block', background: '#000' }}
      />
    </div>
  )
}
