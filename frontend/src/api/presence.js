import apiClient from './client'

export const presenceApi = {
  getPresence: () => apiClient.get('/presence'),
  getCursors: () => apiClient.get('/presence/cursors'),
  getEvents: (since = 0) => apiClient.get('/presence/events', { params: { since } }),
  reset: () => apiClient.post('/presence/reset'),
}
