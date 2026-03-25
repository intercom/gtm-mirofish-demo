import client from './client'

export const scenariosApi = {
  list: () => client.get('/gtm/scenarios'),
  get: (scenarioId) => client.get(`/gtm/scenarios/${scenarioId}`),
  getSeedData: (dataType) => client.get(`/gtm/seed-data/${dataType}`),
  getSeedText: (scenarioId) =>
    client.get(`/gtm/scenarios/${scenarioId}/seed-text`),
  importScenario: (scenarioData) =>
    client.post('/gtm/scenarios/import', scenarioData),
}
