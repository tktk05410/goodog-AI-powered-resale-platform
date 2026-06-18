import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.role === 'admin')

  async function login(username, password) {
    const res = await api.post('/auth/login', { username, password })
    token.value = res.data.token
    userInfo.value = res.data.user
    localStorage.setItem('token', token.value)
    return res.data
  }

  async function register(username, password, student_id) {
    const res = await api.post('/auth/register', { username, password, student_id })
    token.value = res.data.token
    userInfo.value = res.data.user
    localStorage.setItem('token', token.value)
    return res.data
  }

  async function fetchUserInfo() {
    if (!token.value) return null
    try {
      const res = await api.get('/auth/me')
      userInfo.value = res.data.user
      return userInfo.value
    } catch (e) {
      logout()
      return null
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    isAdmin,
    login,
    register,
    fetchUserInfo,
    logout
  }
})