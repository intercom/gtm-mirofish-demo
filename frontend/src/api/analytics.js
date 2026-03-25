import client from './client'

export const analyticsApi = {
  getSegments: (type = 'plan_tier') =>
    client.get('/v1/analytics/segments', { params: { type } }),

  getSegmentAccounts: (segmentType, segmentName) =>
    client.get(`/v1/analytics/segments/${segmentType}/${encodeURIComponent(segmentName)}/accounts`),
}
