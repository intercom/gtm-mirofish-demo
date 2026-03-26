import client from './client'

export const scenariosApi = {
  list: () => client.get('/gtm/scenarios'),
  get: (scenarioId) => client.get(`/gtm/scenarios/${scenarioId}`),
  getSeedData: (dataType) => client.get(`/gtm/seed-data/${dataType}`),
  getSeedText: (scenarioId) =>
    client.get(`/gtm/scenarios/${scenarioId}/seed-text`),
  getLeaderboard: (runs = []) =>
    client.post('/gtm/scenarios/leaderboard', { runs }),
  getOutcomes: (scenarioId) => client.get(`/gtm/outcomes/${scenarioId}`),
  importScenario: (scenarioData) =>
    client.post('/gtm/scenarios/import', scenarioData),
  getContext: (scenarioId) =>
    client.get(`/gtm/scenarios/${scenarioId}/context`),
  getWalkthrough: (scenarioId) =>
    client.get(`/gtm/scenarios/${scenarioId}/walkthrough`),
}
