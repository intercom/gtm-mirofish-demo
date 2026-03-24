import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_URL || 'https://backend-production-e9d7.up.railway.app/api'

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Inject auth token when available
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Normalize errors so callers always get { message, status, data }
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
      return Promise.reject(error)
    }

    const normalized = {
      message:
        error.response?.data?.error ||
        error.response?.data?.message ||
        error.message ||
        'Network error',
      status: error.response?.status || 0,
      data: error.response?.data || null,
    }
    return Promise.reject(normalized)
  },
)

export default client
