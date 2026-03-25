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
    vi.clearAllMocks()
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

  it('registers a response interceptor', async () => {
    await import('../client')
    const instance = axios.create.mock.results[0].value
    expect(instance.interceptors.response.use).toHaveBeenCalledTimes(1)
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

  it('uses error.response.data.message as fallback', async () => {
    await import('../client')
    const instance = axios.create.mock.results[0].value
    const errorHandler = instance.interceptors.response.use.mock.calls[0][1]

    const error = {
      response: { status: 400, data: { message: 'Bad request' } },
    }

    await expect(errorHandler(error)).rejects.toEqual({
      message: 'Bad request',
      status: 400,
      data: { message: 'Bad request' },
    })
  })

  it('defaults message to "Network error" when no info available', async () => {
    await import('../client')
    const instance = axios.create.mock.results[0].value
    const errorHandler = instance.interceptors.response.use.mock.calls[0][1]

    const error = {}

    await expect(errorHandler(error)).rejects.toEqual({
      message: 'Network error',
      status: 0,
      data: null,
    })
  })
})
