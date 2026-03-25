import client from './client'

export const comparisonApi = {
  listRuns: () => client.get('/v1/comparison/runs'),
  getData: (runIds, metric) =>
    client.post('/v1/comparison/data', {
      run_ids: runIds,
      ...(metric && { metric }),
    }),
}
