import client from './client'

export const campaignsApi = {
  list: (params) => client.get('/campaigns', { params }),
  get: (campaignId) => client.get(`/campaigns/${campaignId}`),
  stats: () => client.get('/campaigns/stats'),
  roiComparison: () => client.get('/campaigns/roi-comparison'),
  attribution: (model) => client.get(`/campaigns/attribution/${model}`),
  attributionComparison: () => client.get('/campaigns/attribution'),
  budgetEfficiency: () => client.get('/campaigns/budget-efficiency'),
}

export function fetchAttributionComparison() {
  return client.get('/campaigns/attribution')
}
