import client from './client'

export const insightsApi = {
  get: (params) => client.get('/insights', { params }),
  generate: (data) => client.post('/insights', data),
  types: () => client.get('/insights/types'),
  chat: (data) => client.post('/insights/chat', data),
}
