import client from './client'

export const salesforceApi = {
  getStats: () => client.get('/salesforce/stats'),
}
