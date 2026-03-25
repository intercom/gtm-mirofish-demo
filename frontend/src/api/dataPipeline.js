import client from './client'

export const dataPipelineApi = {
  getConnectors: () => client.get('/v1/pipeline/connectors'),
}
