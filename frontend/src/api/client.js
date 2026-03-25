import axios from 'axios'
import { perfMonitor } from '../lib/perfMonitor'

export const API_BASE = import.meta.env.VITE_API_URL || '/api'

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

perfMonitor.createAxiosTimingInterceptors(client)

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
