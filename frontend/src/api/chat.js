import client from './client'

// Chat with the report agent (analysis Q&A)
export function chatWithReport({ simulationId, message, chatHistory }) {
  return client.post('/report/chat', {
    simulation_id: simulationId,
    message,
    chat_history: chatHistory,
  })
}

// Interview a single simulation agent
export function interview({ simulationId, agentName, prompt }) {
  return client.post('/simulation/interview', {
    simulation_id: simulationId,
    agent_name: agentName,
    prompt,
  })
}

// Interview multiple agents in batch
export function interviewBatch({ simulationId, agentNames, prompt }) {
  return client.post('/simulation/interview/batch', {
    simulation_id: simulationId,
    agent_names: agentNames,
    prompt,
  })
}

// Interview all agents
export function interviewAll({ simulationId, prompt }) {
  return client.post('/simulation/interview/all', {
    simulation_id: simulationId,
    prompt,
  })
}

// Get interview history for a simulation
export function getInterviewHistory({ simulationId, agentName }) {
  return client.post('/simulation/interview/history', {
    simulation_id: simulationId,
    agent_name: agentName,
  })
}
