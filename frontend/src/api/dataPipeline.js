import client from './client'

export const dataPipelineApi = {
  getSyncs: (params) => client.get('/pipeline/syncs', { params }),
  getSync: (syncId) => client.get(`/pipeline/syncs/${syncId}`),
  getConnectors: () => client.get('/v1/pipeline/connectors'),
  getDbtModels: () => client.get('/pipeline/dbt/models'),
  getDbtDag: () => client.get('/pipeline/dbt/dag'),
  getDbtTests: (params) => client.get('/pipeline/dbt/tests', { params }),
  getFreshness: () => client.get('/pipeline/freshness'),
  getStats: () => client.get('/pipeline/stats'),
}
