import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'

vi.mock('axios', () => {
  const interceptors = {
    request: { use: vi.fn() },
    response: { use: vi.fn() },
  }
  const instance = {
    interceptors,
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    defaults: { headers: { common: {} } },
  }
  return {
    default: { create: vi.fn(() => instance) },
  }
})

describe('client', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('creates axios instance with correct baseURL and headers', async () => {
    await import('../client')
    expect(axios.create).toHaveBeenCalledWith({
      baseURL: '/api',
      headers: { 'Content-Type': 'application/json' },
    })
  })

  it('registers request and response interceptors', async () => {
    const { default: client } = await import('../client')
    expect(client.interceptors.request.use).toHaveBeenCalled()
    expect(client.interceptors.response.use).toHaveBeenCalled()
  })

  describe('request interceptor', () => {
    it('injects auth token when present in localStorage', async () => {
      const { default: client } = await import('../client')
      const calls = client.interceptors.request.use.mock.calls
      const requestInterceptor = calls[calls.length - 1][0]

      localStorage.setItem('auth_token', 'test-token-123')
      const config = { headers: {} }
      const result = requestInterceptor(config)

      expect(result.headers.Authorization).toBe('Bearer test-token-123')
    })

    it('does not inject auth header when no token', async () => {
      const { default: client } = await import('../client')
      const calls = client.interceptors.request.use.mock.calls
      const requestInterceptor = calls[calls.length - 1][0]

      const config = { headers: {} }
      const result = requestInterceptor(config)

      expect(result.headers.Authorization).toBeUndefined()
    })
  })

  describe('response error interceptor', () => {
    it('clears token and redirects on 401', async () => {
      const { default: client } = await import('../client')
      const calls = client.interceptors.response.use.mock.calls
      const errorHandler = calls[calls.length - 1][1]

      localStorage.setItem('auth_token', 'old-token')

      // Mock window.location
      const originalLocation = window.location
      delete window.location
      window.location = { href: '' }

      const error = { response: { status: 401 } }
      await expect(errorHandler(error)).rejects.toEqual(error)

      expect(localStorage.getItem('auth_token')).toBeNull()
      expect(window.location.href).toBe('/login')

      window.location = originalLocation
    })

    it('rejects non-401 errors without redirect', async () => {
      const { default: client } = await import('../client')
      const calls = client.interceptors.response.use.mock.calls
      const errorHandler = calls[calls.length - 1][1]

      localStorage.setItem('auth_token', 'my-token')
      const error = { response: { status: 500 } }
      await expect(errorHandler(error)).rejects.toEqual(error)

      expect(localStorage.getItem('auth_token')).toBe('my-token')
    })
  })
})
