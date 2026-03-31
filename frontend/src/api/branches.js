import client from './client'

export const branchesApi = {
  getInsights: (data) => client.post('/branches/insights', data),
}
