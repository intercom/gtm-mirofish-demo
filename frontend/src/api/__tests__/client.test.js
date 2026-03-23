// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
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
    delete: vi.fn(),
  }
  return {
    default: { create: vi.fn(() => instance) },
  }
})

describe('client', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('creates an axios instance with /api baseURL', async () => {
    await import('../client')
    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({ baseURL: '/api' }),
    )
  })

  it('sets Content-Type to application/json', async () => {
    await import('../client')
    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({
        headers: { 'Content-Type': 'application/json' },
      }),
    )
  })

  it('registers request and response interceptors', async () => {
    await import('../client')
    const instance = axios.create.mock.results[0].value
    expect(instance.interceptors.request.use).toHaveBeenCalledTimes(1)
    expect(instance.interceptors.response.use).toHaveBeenCalledTimes(1)
  })

  it('injects auth token from localStorage in request interceptor', async () => {
    await import('../client')
    const instance = axios.create.mock.results[0].value
    const requestHandler = instance.interceptors.request.use.mock.calls[0][0]

    localStorage.setItem('auth_token', 'test-token-123')
    const config = { headers: {} }
    const result = requestHandler(config)
    expect(result.headers.Authorization).toBe('Bearer test-token-123')
  })

  it('does not set Authorization header when no token exists', async () => {
    await import('../client')
    const instance = axios.create.mock.results[0].value
    const requestHandler = instance.interceptors.request.use.mock.calls[0][0]

    const config = { headers: {} }
    const result = requestHandler(config)
    expect(result.headers.Authorization).toBeUndefined()
  })

  it('normalizes error responses in response interceptor', async () => {
    await import('../client')
    const instance = axios.create.mock.results[0].value
    const errorHandler = instance.interceptors.response.use.mock.calls[0][1]

    const error = {
      response: { status: 500, data: { error: 'Server error' } },
      message: 'Request failed',
    }

    await expect(errorHandler(error)).rejects.toEqual({
      message: 'Server error',
      status: 500,
      data: { error: 'Server error' },
    })
  })

  it('clears token on 401 and attempts redirect', async () => {
    await import('../client')
    const instance = axios.create.mock.results[0].value
    const errorHandler = instance.interceptors.response.use.mock.calls[0][1]

    localStorage.setItem('auth_token', 'expired')

    const error = {
      response: { status: 401, data: { error: 'Unauthorized' } },
    }

    await expect(errorHandler(error)).rejects.toBeDefined()
    expect(localStorage.getItem('auth_token')).toBeNull()
  })

  it('handles network errors without response', async () => {
    await import('../client')
    const instance = axios.create.mock.results[0].value
    const errorHandler = instance.interceptors.response.use.mock.calls[0][1]

    const error = { message: 'Network Error' }

    await expect(errorHandler(error)).rejects.toEqual({
      message: 'Network Error',
      status: 0,
      data: null,
    })
  })
})
