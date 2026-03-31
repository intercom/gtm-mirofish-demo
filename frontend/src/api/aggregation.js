import client from './client'

export const aggregationApi = {
  /**
   * Aggregate metrics across multiple simulations.
   * @param {string[]} ids - Simulation IDs
   * @param {string} mode - 'metrics'|'common'|'rare'|'ci'|'cluster'|'all'
   * @param {object} params - Additional params (e.g. { metric: 'total_actions' } for ci mode)
   */
  aggregate: (ids, mode = 'metrics', params = {}) =>
    client.get('/simulations/aggregate', {
      params: { ids: ids.join(','), mode, ...params },
    }),
}
