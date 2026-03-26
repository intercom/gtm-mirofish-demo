import client from './client'

export const analyticsApi = {
  // --- Cohort analysis ---
  getCohorts: (params) => client.get('/v1/analytics/cohorts', { params }),
  compareCohorts: (params) => client.get('/v1/analytics/cohorts/compare', { params }),
}
