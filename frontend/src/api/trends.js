import client from './client'

export const trendsApi = {
  getScenarioTrends: () => client.get('/gtm/scenarios/trends'),
}
