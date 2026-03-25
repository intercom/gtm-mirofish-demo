import client from './client'

export const pipelineApi = {
  getForecast: () => client.get('/pipeline/forecast'),
}
