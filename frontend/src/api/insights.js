import client from './client'

export const insightsApi = {
  get: (params) => client.get('/v1/insights', { params }),
  generate: (data) => client.post('/v1/insights', data),
  types: () => client.get('/v1/insights/types'),
}
