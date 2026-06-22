import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { videoApi, subApi, balanceApi } from '../api/client'
import { Btn, Input, Textarea, Select, Modal, Spinner, Empty, Card, SectionTitle, Badge, Tabs, useToast } from '../components/ui'
import { useAuthStore } from '../store/auth'

const VISIBILITY_OPTIONS = [
  { value: 'PUBLIC', label: '🌍 Public' },
  { value: 'SUBSCRIPTION', label: '🔐 Subscription only' },
  { value: 'PRIVATE', label: '🔒 Private' },
]

const VIS_COLOR = { PUBLIC: 'var(--green)', SUBSCRIPTION: 'var(--accent)', PRIVATE: 'var(--text3)' }
const STATUS_COLOR = { READY: 'var(--green)', DRAFT: 'var(--text3)', PROCESSING: 'var(--yellow)', FAILED: 'var(--red)' }

export default function StudioPage() {
  const { user } = useAuthStore()
  const nav = useNavigate()
  const toast = useToast()
  const [tab, setTab] = useState('videos')
  const [videos, setVideos] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploadModal, setUploadModal] = useState(false)
  const [editModal, setEditModal] = useState(null)
  const [subModal, setSubModal] = useState(false)
  const [balance, setBalance] = useState(null)   // null = не загружен, false = нет баланса
  const [hasSub, setHasSub] = useState(false)

  useEffect(() => {
    if (!user) { nav('/login'); return }
    loadAll()
  }, [user])

  const loadAll = async () => {
    setLoading(true)
    try {
      const [videosRes, subIdRes] = await Promise.all([
        videoApi.mine(),
        subApi.idByAuthor(user.id),
      ])
      setVideos(videosRes.data)

      if (subIdRes.data.subscription_id) {
        setHasSub(true)
        try {
          const { data: bal } = await balanceApi.get()
          setBalance(bal)
        } catch {
          setBalance(false) // 404 — баланс ещё не создан
        }
      }
    } catch {}
    setLoading(false)
  }

  const handleDelete = async id => {
    if (!confirm('Delete this video? This cannot be undone.')) return
    try {
      await videoApi.delete(id)
      setVideos(v => v.filter(x => x.id !== id))
      toast('Video deleted', 'success')
    } catch (e) { toast(e.friendlyMessage || 'Error', 'error') }
  }

  if (!user) return null

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '2rem 1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 800 }}>Studio</h1>
          <p style={{ color: 'var(--text2)', fontSize: '.875rem' }}>Manage your content</p>
        </div>
        <div style={{ display: 'flex', gap: '.75rem', alignItems: 'center' }}>
          {hasSub && balance && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: '.5rem',
              background: 'rgba(45,204,133,.08)', border: '1px solid rgba(45,204,133,.25)',
              borderRadius: 'var(--radius)', padding: '.45rem .9rem',
            }}>
              <span style={{ fontSize: '.8rem', color: 'var(--text3)' }}>Balance</span>
              <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, color: 'var(--green)', fontSize: '1rem' }}>
                {Number(balance.amount).toLocaleString('ru')} ₽
              </span>
            </div>
          )}
          <Btn variant="ghost" onClick={() => setSubModal(true)}>Subscriptions</Btn>
          <Btn onClick={() => setUploadModal(true)}>+ Upload video</Btn>
        </div>
      </div>

      <Tabs
        tabs={[{ value: 'videos', label: 'My Videos' }, { value: 'stats', label: 'Overview' }]}
        active={tab}
        onChange={setTab}
      />

      <div style={{ marginTop: '1.5rem' }}>
        {tab === 'videos' && (
          loading
            ? <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}><Spinner size={36} /></div>
            : videos.length === 0
              ? <Empty icon="🎬" text="You haven't uploaded any videos yet" />
              : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '.75rem' }}>
                  {videos.map(v => (
                    <VideoRow
                      key={v.id}
                      video={v}
                      onEdit={() => setEditModal(v)}
                      onDelete={() => handleDelete(v.id)}
                      onWatch={() => nav(`/watch/${v.id}`)}
                    />
                  ))}
                </div>
              )
        )}
        {tab === 'stats' && <StatsOverview videos={videos} />}
      </div>

      <UploadModal
        open={uploadModal}
        onClose={() => setUploadModal(false)}
        onCreated={v => { setVideos(vs => [v, ...vs]); setUploadModal(false) }}
      />
      {editModal && (
        <EditModal
          video={editModal}
          onClose={() => setEditModal(null)}
          onSaved={updated => {
            setVideos(vs => vs.map(v => v.id === updated.id ? updated : v))
            setEditModal(null)
          }}
        />
      )}
      <SubscriptionModal open={subModal} onClose={() => setSubModal(false)} userId={user.id} />
    </div>
  )
}

function VideoRow({ video, onEdit, onDelete, onWatch }) {
  const [hov, setHov] = useState(false)
  return (
    <div
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        display: 'flex', alignItems: 'center', gap: '1rem',
        background: hov ? 'var(--surface2)' : 'var(--surface)',
        border: '1px solid var(--border)', borderRadius: 'var(--radius)',
        padding: '.75rem 1rem', transition: 'all var(--transition)'
      }}
    >
      <div style={{
        width: 80, height: 45, borderRadius: 6, background: 'var(--surface3)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '1.2rem', flexShrink: 0, overflow: 'hidden'
      }}>
        {video.preview_url
          ? <img src={video.preview_url} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          : 'CLAP'
        }
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontWeight: 600, fontSize: '.9375rem', fontFamily: 'var(--font-display)',
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
        }}>
          {video.title}
        </div>
        <div style={{ display: 'flex', gap: '.5rem', marginTop: '.25rem', flexWrap: 'wrap' }}>
          <Badge color={STATUS_COLOR[video.processing_status]}>{video.processing_status}</Badge>
          <Badge color={VIS_COLOR[video.visibility]}>{video.visibility}</Badge>
        </div>
      </div>
      <div style={{ display: 'flex', gap: '.5rem', flexShrink: 0 }}>
        <Btn size="sm" variant="ghost" onClick={onWatch}>Watch</Btn>
        <Btn size="sm" variant="secondary" onClick={onEdit}>Edit</Btn>
        <Btn size="sm" variant="danger" onClick={onDelete}>Delete</Btn>
      </div>
    </div>
  )
}

function UploadModal({ open, onClose, onCreated }) {
  const toast = useToast()
  const [step, setStep] = useState(1)
  const [form, setForm] = useState({ title: '', description: '', visibility: 'PUBLIC' })
  const [creating, setCreating] = useState(false)
  const [videoId, setVideoId] = useState(null)
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [processing, setProcessing] = useState(false)
  const [previewFile, setPreviewFile] = useState(null)
  const fileRef = useRef()
  const prevRef = useRef()

  const reset = () => {
    setStep(1)
    setForm({ title: '', description: '', visibility: 'PUBLIC' })
    setVideoId(null); setFile(null); setProgress(0); setPreviewFile(null)
  }

  const handleClose = () => { onClose(); reset() }
  const setField = key => e => setForm(f => ({ ...f, [key]: e.target.value }))

  const createVideo = async () => {
  if (!form.title.trim()) return
  setCreating(true)

  try {
    const { data } = await videoApi.create({
      title: form.title,
      description: form.description
    })

    await videoApi.update(data.id, {
      title: form.title,
      description: form.description,
      visibility: form.visibility,
    })

    setVideoId(data.id)
    setStep(2)

  } catch (e) {
    const code = e?.response?.data?.error?.code

    if (
      code === 'SUBSCRIPTION_NOT_EXISTS' ||
      code === 'BALANCE_NOT_EXISTS'
    ) {
      toast(
        'Для доступа к подписочным видео нужно:\n' +
        'Создать подписку\n',
        'error'
      )
      return
    }

    if (code === 'SUBSCRIPTION_EXPIRE') {
      toast(
        'Подписка истекла. Обновите подписку и убедитесь, что баланс активен.',
        'error'
      )
      return
    }

    toast(e?.friendlyMessage || 'Error creating video', 'error')
  }

  setCreating(false)
}

  const uploadVideo = async () => {
    if (!file || !videoId) return
    setUploading(true)
    try {
      const { data } = await videoApi.uploadUrl(videoId)
      await axios.put(data.upload_url, file, {
        headers: { 'Content-Type': file.type },
        onUploadProgress: e => setProgress(Math.round(e.loaded * 100 / e.total)),
      })
      toast('Video uploaded!', 'success')
      setStep(3)
    } catch { toast('Upload failed', 'error') }
    setUploading(false)
  }

  const processVideo = async () => {
    setProcessing(true)
    try {
      if (previewFile) {
        const { data } = await videoApi.previewUploadUrl(videoId)
        await axios.put(data.upload_url, previewFile, { headers: { 'Content-Type': previewFile.type } })
        await videoApi.updatePreview(videoId, data.key)
      }
      await videoApi.process(videoId)
      toast('Processing started!', 'success')
      const { data } = await videoApi.one(videoId)
      onCreated(data)
      reset()
    } catch (e) { toast(e.friendlyMessage || 'Error', 'error') }
    setProcessing(false)
  }

  return (
    <Modal open={open} onClose={handleClose} title="Upload video" width={520}>
      <div style={{ display: 'flex', gap: '.25rem', marginBottom: '1.5rem' }}>
        {['Info & visibility', 'Upload', 'Finalize'].map((s, i) => (
          <div key={s} style={{
            flex: 1, height: 3, borderRadius: 3,
            background: step > i ? 'var(--accent)' : 'var(--surface3)',
            transition: 'background .3s'
          }} />
        ))}
      </div>

      {step === 1 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <Input label="Title" value={form.title} onChange={setField('title')} placeholder="Video title" />
          <Textarea label="Description" value={form.description} onChange={setField('description')} placeholder="Describe your video..." />
          <Select label="Visibility" value={form.visibility} onChange={setField('visibility')}>
            {VISIBILITY_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </Select>
          {form.visibility === 'SUBSCRIPTION' && (
            <div style={{
              background: 'rgba(124,92,252,.08)', border: '1px solid rgba(124,92,252,.25)',
              borderRadius: 'var(--radius)', padding: '.65rem .9rem',
              fontSize: '.8125rem', color: 'var(--text2)'
            }}>
              Subscription videos are only visible to your subscribers. Make sure you have a plan set up.
            </div>
          )}
          <Btn onClick={createVideo} loading={creating} full>Continue</Btn>
        </div>
      )}

      {step === 2 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div>
            <label style={{ fontSize: '.8125rem', color: 'var(--text2)', fontWeight: 500, display: 'block', marginBottom: '.35rem' }}>Video file</label>
            <div onClick={() => fileRef.current.click()} style={{
              border: `2px dashed ${file ? 'var(--accent)' : 'var(--border)'}`,
              borderRadius: 'var(--radius)', padding: '2rem', textAlign: 'center',
              cursor: 'pointer', transition: 'all var(--transition)',
              background: file ? 'rgba(124,92,252,.05)' : 'transparent',
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '.5rem' }}>VID</div>
              <div style={{ fontSize: '.875rem', color: file ? 'var(--accent)' : 'var(--text2)' }}>
                {file ? file.name : 'Click to select video file'}
              </div>
            </div>
            <input ref={fileRef} type="file" accept="video/*" style={{ display: 'none' }} onChange={e => setFile(e.target.files[0])} />
          </div>

          <div>
            <label style={{ fontSize: '.8125rem', color: 'var(--text2)', fontWeight: 500, display: 'block', marginBottom: '.35rem' }}>Thumbnail (optional)</label>
            <div onClick={() => prevRef.current.click()} style={{
              border: `2px dashed ${previewFile ? 'var(--green)' : 'var(--border)'}`,
              borderRadius: 'var(--radius)', padding: '1rem', textAlign: 'center',
              cursor: 'pointer', transition: 'all var(--transition)',
            }}>
              <div style={{ fontSize: '.875rem', color: previewFile ? 'var(--green)' : 'var(--text2)' }}>
                IMG {previewFile ? previewFile.name : 'Click to select thumbnail'}
              </div>
            </div>
            <input ref={prevRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={e => setPreviewFile(e.target.files[0])} />
          </div>

          {uploading && (
            <div>
              <div style={{ height: 4, background: 'var(--surface3)', borderRadius: 2, overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${progress}%`, background: 'var(--accent)', transition: 'width .2s', borderRadius: 2 }} />
              </div>
              <div style={{ fontSize: '.8rem', color: 'var(--text2)', marginTop: '.35rem', textAlign: 'center' }}>{progress}%</div>
            </div>
          )}

          <Btn onClick={uploadVideo} loading={uploading} disabled={!file} full>Upload</Btn>
        </div>
      )}

      {step === 3 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', textAlign: 'center' }}>
          <div style={{ fontSize: '3rem' }}>OK</div>
          <h3 style={{ fontFamily: 'var(--font-display)' }}>Video uploaded!</h3>
          <p style={{ color: 'var(--text2)', fontSize: '.875rem' }}>
            Click Process to start encoding. This may take a few minutes.
          </p>
          <Btn onClick={processVideo} loading={processing} full>Start processing</Btn>
        </div>
      )}
    </Modal>
  )
}

// Visibility is intentionally read-only here — set at upload time only.
function EditModal({ video, onClose, onSaved }) {
  const toast = useToast()
  const [form, setForm] = useState({ title: video.title, description: video.description })
  const [saving, setSaving] = useState(false)
  const [prevFile, setPrevFile] = useState(null)
  const prevRef = useRef()

  const save = async () => {
    setSaving(true)
    try {
      if (prevFile) {
        const { data } = await videoApi.previewUploadUrl(video.id)
        await axios.put(data.upload_url, prevFile, { headers: { 'Content-Type': prevFile.type } })
        await videoApi.updatePreview(video.id, data.key)
      }
      await videoApi.update(video.id, {
        title: form.title,
        description: form.description,
        visibility: video.visibility, // pass through unchanged
      })
      toast('Saved!', 'success')
      onSaved({ ...video, ...form })
    } catch (e) { toast(e.friendlyMessage || 'Error', 'error') }
    setSaving(false)
  }

  return (
    <Modal open title="Edit video" onClose={onClose}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <Input label="Title" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
        <Textarea label="Description" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />

        <div style={{ display: 'flex', flexDirection: 'column', gap: '.35rem' }}>
          <label style={{ fontSize: '.8125rem', color: 'var(--text2)', fontWeight: 500 }}>Visibility</label>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '.75rem',
            padding: '.65rem 1rem', background: 'var(--surface2)',
            border: '1.5px solid var(--border)', borderRadius: 'var(--radius)',
          }}>
            <Badge color={VIS_COLOR[video.visibility]}>{video.visibility}</Badge>
            <span style={{ fontSize: '.8125rem', color: 'var(--text3)' }}>Set at upload — cannot be changed</span>
          </div>
        </div>

        <div>
          <label style={{ fontSize: '.8125rem', color: 'var(--text2)', fontWeight: 500, display: 'block', marginBottom: '.35rem' }}>Update thumbnail</label>
          <div onClick={() => prevRef.current.click()} style={{
            border: '2px dashed var(--border)', borderRadius: 'var(--radius)',
            padding: '.75rem', textAlign: 'center', cursor: 'pointer',
            fontSize: '.875rem', color: 'var(--text2)',
          }}>
            {prevFile ? prevFile.name : 'IMG Click to change thumbnail'}
          </div>
          <input ref={prevRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={e => setPrevFile(e.target.files[0])} />
        </div>

        <div style={{ display: 'flex', gap: '.75rem' }}>
          <Btn variant="ghost" onClick={onClose} full>Cancel</Btn>
          <Btn onClick={save} loading={saving} full>Save</Btn>
        </div>
      </div>
    </Modal>
  )
}

function SubscriptionModal({ open, onClose, userId }) {
  const toast = useToast()
  const [sub, setSub] = useState(null)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ days: 30, price: 299 })
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    if (!open || !userId) return
    setLoading(true)
    subApi.idByAuthor(userId)
      .then(async ({ data }) => {
        if (data.subscription_id) {
          const { data: s } = await subApi.byId(data.subscription_id)
          setSub(s.author_sub)
        }
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [open, userId])

  const create = async () => {
    setCreating(true)
    try {
      await subApi.create(form)
      toast('Subscription plan created!', 'success')
      const { data } = await subApi.idByAuthor(userId)
      if (data.subscription_id) {
        const { data: s } = await subApi.byId(data.subscription_id)
        setSub(s.author_sub)
      }
    } catch (e) { toast(e.friendlyMessage || 'Error', 'error') }
    setCreating(false)
  }

  return (
    <Modal open={open} onClose={onClose} title="Subscription settings">
      {loading
        ? <div style={{ textAlign: 'center' }}><Spinner /></div>
        : sub
          ? (
            <div>
              <p style={{ color: 'var(--text2)', marginBottom: '1rem' }}>Your current subscription plan:</p>
              <div style={{ display: 'flex', gap: '1.5rem', background: 'var(--surface2)', borderRadius: 'var(--radius)', padding: '1rem' }}>
                <div>
                  <div style={{ fontSize: '.8rem', color: 'var(--text3)' }}>Duration</div>
                  <div style={{ fontWeight: 700, fontFamily: 'var(--font-display)' }}>{sub.days} days</div>
                </div>
                <div>
                  <div style={{ fontSize: '.8rem', color: 'var(--text3)' }}>Price</div>
                  <div style={{ fontWeight: 700, color: 'var(--accent)', fontFamily: 'var(--font-display)' }}>{sub.price} RUB</div>
                </div>
              </div>
              <p style={{ color: 'var(--text3)', fontSize: '.8125rem', marginTop: '1rem' }}>To change the plan, contact support.</p>
            </div>
          )
          : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <p style={{ color: 'var(--text2)', fontSize: '.875rem' }}>Create a subscription plan so fans can access your exclusive videos.</p>
              <Input label="Duration (days)" type="number" min={1} value={form.days} onChange={e => setForm(f => ({ ...f, days: +e.target.value }))} />
              <Input label="Price (RUB)" type="number" min={1} value={form.price} onChange={e => setForm(f => ({ ...f, price: +e.target.value }))} />
              <Btn onClick={create} loading={creating} full>Create plan</Btn>
            </div>
          )
      }
    </Modal>
  )
}

function StatsOverview({ videos }) {
  const stats = [
    { label: 'Total videos', value: videos.length, icon: 'VID' },
    { label: 'Published', value: videos.filter(v => v.processing_status === 'READY').length, icon: 'OK' },
    { label: 'Public', value: videos.filter(v => v.visibility === 'PUBLIC').length, icon: 'PUB' },
    { label: 'Subscription', value: videos.filter(v => v.visibility === 'SUBSCRIPTION').length, icon: 'SUB' },
  ]
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '1rem' }}>
      {stats.map(s => (
        <Card key={s.label} style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '1.5rem', marginBottom: '.5rem', color: 'var(--text3)' }}>{s.icon}</div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: 800, color: 'var(--accent)' }}>{s.value}</div>
          <div style={{ color: 'var(--text2)', fontSize: '.8125rem' }}>{s.label}</div>
        </Card>
      ))}
    </div>
  )
}