import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_URL || '/api'

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

// Attach CSRF token from cookie to state-changing requests
client.interceptors.request.use((config) => {
  const method = config.method?.toUpperCase()
  if (method && method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS') {
    const token = getCookie('csrf_token')
    if (token) {
      config.headers['X-CSRFToken'] = token
    }
  }
  return config
})

// Normalize errors so callers always get { message, status, data }
client.interceptors.response.use(
  (response) => response,
  (error) => {
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
