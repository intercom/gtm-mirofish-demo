import client from './client'

export const activityApi = {
  getRecent: (params = {}) => client.get('/activity', { params }),
}
