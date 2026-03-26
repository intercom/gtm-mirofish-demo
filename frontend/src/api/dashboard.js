import client from './client'

export const dashboardApi = {
  getTopAccounts: (params) => client.get('/gtm/dashboard/top-accounts', { params }),
}
