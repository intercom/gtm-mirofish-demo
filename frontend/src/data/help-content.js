/**
 * Contextual help content database.
 * Maps feature keys to help entries displayed by ContextualHelp.vue.
 */

export const helpContent = {
  'oasis-simulation': {
    title: 'OASIS Simulation',
    description:
      'OASIS (Open Agent Social Interaction Simulations) runs AI agents that mimic real stakeholders — buyers, champions, detractors — interacting on simulated social platforms. Each agent has a unique persona and reacts to others, producing emergent group behavior you can analyze.',
    learnMoreUrl: 'https://github.com/camel-ai/oasis',
  },
  'knowledge-graph': {
    title: 'Zep Knowledge Graph',
    description:
      'The knowledge graph extracts entities (people, companies, products) and relationships from your seed text using an LLM. Zep stores these as nodes and edges, giving the simulation structured world knowledge that agents can reference during conversations.',
    learnMoreUrl: 'https://www.getzep.com/',
  },
  'personality-dynamics': {
    title: 'Personality Dynamics',
    description:
      'Each simulated agent is assigned personality traits (openness, agreeableness, assertiveness) that influence how they react to information. Over rounds, agents shift sentiment based on peer interactions — modeling real-world opinion change in buying committees.',
    learnMoreUrl: null,
  },
  'coalition-detection': {
    title: 'Coalition Detection',
    description:
      'The engine identifies clusters of agents that align on position, sentiment, or topic over time. Coalitions reveal which stakeholders are likely allies or blockers in a deal — surfacing political dynamics that are invisible in traditional pipeline tools.',
    learnMoreUrl: null,
  },
  'what-if-analysis': {
    title: 'What-If Analysis',
    description:
      'Run alternative simulation branches by changing variables — swap a competitor mention, adjust an agent\'s initial sentiment, or introduce a new stakeholder mid-simulation. Compare outcomes across branches to stress-test your GTM strategy.',
    learnMoreUrl: null,
  },
  'scenario-branching': {
    title: 'Scenario Branching',
    description:
      'Create multiple simulation scenarios from the same seed data with different parameters (agent count, persona mix, platform mode). Each branch runs independently, letting you A/B test GTM approaches like messaging changes or competitive positioning.',
    learnMoreUrl: null,
  },
  'd3-visualizations': {
    title: 'D3 Visualizations',
    description:
      'Interactive charts built with D3.js render simulation data in real time — sentiment timelines, influence networks, engagement heatmaps, and competitive mention tracking. Hover and click to drill into specific agents, rounds, or topics.',
    learnMoreUrl: 'https://d3js.org/',
  },
  'seed-text': {
    title: 'Seed Text',
    description:
      'The seed text is the starting scenario description that the LLM analyzes to build a knowledge graph. It should describe the market context, key players, competitive landscape, and customer dynamics you want to simulate.',
    learnMoreUrl: null,
  },
  'agent-personas': {
    title: 'Agent Personas',
    description:
      'Each AI agent is generated from the knowledge graph with a role (e.g. VP of Engineering, CFO), personality traits, and domain knowledge. Personas determine how agents post, react, and form opinions during the simulation.',
    learnMoreUrl: null,
  },
  'influence-network': {
    title: 'Influence Network',
    description:
      'A directed graph showing how agents influence each other through replies, topic adoption, and sentiment alignment. Edge weight indicates influence strength — thicker connections mean stronger persuasion between agents.',
    learnMoreUrl: null,
  },
  'competitive-mentions': {
    title: 'Competitive Mentions',
    description:
      'Tracks how often competitor names (Zendesk, Freshdesk, HubSpot, Salesforce, Help Scout) appear in agent conversations, who mentions them, and whether the sentiment around each mention is positive, negative, or neutral.',
    learnMoreUrl: null,
  },
  'engagement-heatmap': {
    title: 'Engagement Heatmap',
    description:
      'A matrix visualization showing agent activity intensity across simulation rounds. Rows are agents, columns are time buckets. Hot cells indicate bursts of activity — useful for spotting when specific stakeholders become most engaged.',
    learnMoreUrl: null,
  },
}

export function getHelpContent(key) {
  return helpContent[key] || null
}

export const helpKeys = Object.keys(helpContent)
