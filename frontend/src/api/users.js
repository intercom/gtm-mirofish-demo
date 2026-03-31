import client from './client'

export const usersApi = {
  list: () => client.get('/users'),
  get: (userId) => client.get(`/users/${userId}`),
  create: (data) => client.post('/users', data),
  update: (userId, data) => client.put(`/users/${userId}`, data),
  delete: (userId) => client.delete(`/users/${userId}`),
  roles: () => client.get('/users/roles'),
  updateRole: (email, role) => client.put(`/users/${encodeURIComponent(email)}/role`, { role }),
  remove: (email) => client.delete(`/users/${encodeURIComponent(email)}`),
  invite: (email, name, role) => client.post('/users/invite', { email, name, role }),
}
