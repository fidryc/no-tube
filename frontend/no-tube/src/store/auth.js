import { create } from 'zustand'
import { authApi } from '../api/client'

export const useAuthStore = create((set, get) => ({
  user: null,
  loading: true,

  fetchMe: async () => {
    try {
      const { data } = await authApi.me()
      set({ user: data, loading: false })
    } catch {
      set({ user: null, loading: false })
    }
  },

  login: async (email, password) => {
    await authApi.login({ email, password })
    await get().fetchMe()
  },

  register: async (username, email, password) => {
    await authApi.register({ username, email, password })
    await get().fetchMe()
  },

  logout: async () => {
    await authApi.logout()
    set({ user: null })
  },

  setUser: user => set({ user }),
}))
