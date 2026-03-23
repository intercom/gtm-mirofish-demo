import client from './client'

// ── Projects ────────────────────────────────────

export function getProject(projectId) {
  return client.get(`/graph/project/${projectId}`)
}

export function listProjects(limit) {
  return client.get('/graph/project/list', { params: { limit } })
}

export function deleteProject(projectId) {
  return client.delete(`/graph/project/${projectId}`)
}

export function resetProject(projectId) {
  return client.post(`/graph/project/${projectId}/reset`)
}

// ── Ontology & Graph Building ───────────────────

export function generateOntology(formData) {
  return client.post('/graph/ontology/generate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function buildGraph(data) {
  return client.post('/graph/build', data)
}

// ── Tasks ───────────────────────────────────────

export function getTask(taskId) {
  return client.get(`/graph/task/${taskId}`)
}

export function listTasks() {
  return client.get('/graph/tasks')
}

// ── Graph Data ──────────────────────────────────

export function getGraphData(graphId) {
  return client.get(`/graph/data/${graphId}`)
}

export function deleteGraph(graphId) {
  return client.delete(`/graph/delete/${graphId}`)
}
