import client from './client'

export const teamApi = {
  getPersonas: () => client.get('/gtm/team/personas'),
  autoGenerate: (params) => client.post('/gtm/team/auto-generate', params),
  listTemplates: () => client.get('/gtm/team/templates'),
  saveTemplate: (template) => client.post('/gtm/team/templates', template),
}
