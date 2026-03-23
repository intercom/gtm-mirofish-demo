import client from './client'

export function listScenarios() {
  return client.get('/gtm/scenarios')
}

export function getScenario(scenarioId) {
  return client.get(`/gtm/scenarios/${scenarioId}`)
}

export function getSeedData(dataType) {
  return client.get(`/gtm/seed-data/${dataType}`)
}

export function getScenarioSeedText(scenarioId) {
  return client.get(`/gtm/scenarios/${scenarioId}/seed-text`)
}
