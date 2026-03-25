import client from './client'

export const demoPresetApi = {
  getStatus: () => client.get('/demo-preset'),
  load: () => client.post('/demo-preset/load'),
  getSimulation: () => client.get('/demo-preset/simulation'),
  getReport: () => client.get('/demo-preset/report'),
  getDashboard: () => client.get('/demo-preset/dashboard'),
}
