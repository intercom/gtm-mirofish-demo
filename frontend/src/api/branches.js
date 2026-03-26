import client from './client'

export const branchesApi = {
  getInsights: (data) => client.post('/v1/branches/insights', data),
}
