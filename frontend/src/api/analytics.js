import client from './client'

export const analyticsApi = {
  // --- Cohort analysis ---
  getCohorts: (params) => client.get('/v1/analytics/cohorts', { params }),
  compareCohorts: (params) => client.get('/v1/analytics/cohorts/compare', { params }),

  // --- Segment performance ---
  getSegments: (type = 'plan_tier') =>
    client.get('/v1/analytics/segments', { params: { type } }),

  getSegmentAccounts: (segmentType, segmentName) =>
    client.get(`/v1/analytics/segments/${segmentType}/${encodeURIComponent(segmentName)}/accounts`),
}
