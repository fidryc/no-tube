import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
})

api.interceptors.response.use(
  res => res,
  err => {
    const data = err.response?.data?.error
    const msg = data?.message || 'Unexpected error'
    return Promise.reject({ ...err, friendlyMessage: msg, errorCode: data?.code })
  }
)

export default api

// ── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  me:       ()     => api.get('/user/me'),
  register: body   => api.post('/user/register', body),
  login:    body   => api.post('/user/login', body),
  logout:   ()     => api.post('/user/quit'),
  confirm:  token  => api.get('/user/confirm', { params: { token } }),
  getUser:  id     => api.get(`/user/${id}`),

  googleUrl:        ()     => api.get('/user/google/url'),
  googleCallback:   code   => api.post('/user/google/callback', { code }),
  yandexParams:     ()     => api.get('/user/yandex/query_params'),
  yandexCallback:   token  => api.post('/user/yandex/callback', { access_token: token }),

  avatarUploadUrl:  ()     => api.post('/user/me/avatar/upload-url'),
  updateAvatar:     key    => api.patch('/user/me/avatar', null, { params: { key } }),
  changePassword:   body   => api.patch('/user/change_password', body),
}

// ── Videos ───────────────────────────────────────────────────────────────────
export const videoApi = {
  list:   params  => api.get('/videos/', { params }),
  mine:   ()      => api.get('/videos/me'),
  one:    id      => api.get(`/videos/${id}`),
  status: id      => api.get(`/videos/${id}/status`),
  stats:  id      => api.get(`/videos/${id}/stats`),
  dash:   id      => api.get(`/videos/${id}/dash`),

  create:   body  => api.post('/videos/', body),
  update:   (id, body) => api.patch(`/videos/${id}`, body),
  delete:   id    => api.delete(`/videos/${id}`),

  uploadUrl:   id => api.post(`/videos/${id}/upload-url`),
  process:     id => api.post(`/videos/${id}/process`),

  previewUploadUrl: id      => api.post(`/videos/${id}/preview/upload-url`),
  updatePreview:    (id, preview_key) => api.patch(`/videos/${id}/preview`, { preview_key }),

  watch:      id  => api.post(`/videos/${id}/watch`),
  like:       id  => api.post(`/videos/${id}/likes`),
  unlike:     id  => api.delete(`/videos/${id}/likes`),
  isLiked:    id  => api.get(`/videos/${id}/likes`),
}

// ── Subscriptions ─────────────────────────────────────────────────────────────
export const subApi = {
  create:         body      => api.post('/videos/subscriptions/authors/', body),
  byAuthor:       authorId  => api.get(`/videos/subscriptions/authors/${authorId}`),
  idByAuthor:     authorId  => api.get(`/videos/subscriptions/authors/${authorId}/id`),
  byId:           subId     => api.get(`/videos/subscriptions/${subId}`),
  check:          subId     => api.get(`/videos/subscriptions/authors/${subId}/check`),
  mySubscriptions:()        => api.get('/videos/me/subscriptions'),
}

// ── Payment ───────────────────────────────────────────────────────────────────
export const paymentApi = {
  confirmationToken: subId => axios.post('/api/payment/confirmation_token', null, {
    params: { sub_id: subId },
    withCredentials: true,
  }),
}

// ── Balance ───────────────────────────────────────────────────────────────────
export const balanceApi = {
  get: () => axios.post('/api/payment/balance', null, { withCredentials: true }),
}