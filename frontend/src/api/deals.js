import client from './client'

export const dealsApi = {
  recent: (count = 10) => client.get('/deals/recent', { params: { count } }),
}
