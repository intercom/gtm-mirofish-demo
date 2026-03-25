import client from './client'

export const revenueApi = {
  getCohortRetention: (months = 12) =>
    client.get('/revenue/cohort', { params: { months } }),
}
