import client from './client'

export const analyticsApi = {
  getAnomalies(params = {}) {
    return client.get('/v1/analytics/anomalies', { params })
  },
}
