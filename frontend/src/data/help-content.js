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

/** Alias for tutorial components that import helpEntries */
export const helpEntries = helpContent

/**
 * Welcome tour steps — targets are CSS selectors for elements on the page.
 * Position: where the tooltip appears relative to the target.
 */
export const welcomeTourSteps = [
  {
    target: '[data-tutorial="nav"]',
    title: 'Navigation',
    description:
      'Use the navigation bar to move between the landing page, your simulations list, and settings.',
    position: 'bottom',
  },
  {
    target: '[data-tutorial="simulations"]',
    title: 'Your Simulations',
    description:
      'View and manage all your GTM simulations. Each simulation tracks its status, agents, and results.',
    position: 'bottom',
  },
  {
    target: '[data-tutorial="scenarios"]',
    title: 'Scenario Templates',
    description:
      'Start from pre-built GTM scenarios like Pipeline Review, Competitive Response, or Product Launch to quickly set up simulations.',
    position: 'bottom',
  },
  {
    target: '[data-tutorial="reports"]',
    title: 'Reports & Insights',
    description:
      'After a simulation completes, generate AI-powered reports with sentiment analysis, coalition maps, and strategic recommendations.',
    position: 'left',
  },
  {
    target: '[data-tutorial="settings"]',
    title: 'Settings',
    description:
      'Configure your LLM provider (Claude, GPT-4, Gemini), API keys, and simulation defaults.',
    position: 'bottom',
  },
]

/**
 * Scenario walkthrough steps — pre-scripted guided demo.
 */
export const walkthroughSteps = [
  {
    id: 'select-template',
    title: 'Select a Template',
    narration: 'Start by choosing the "Pipeline Review" scenario template. This simulates a cross-functional GTM team reviewing pipeline health.',
    actionLabel: 'Select Pipeline Review',
    route: '/',
    estimatedSeconds: 10,
  },
  {
    id: 'configure-agents',
    title: 'Configure Agents',
    narration: 'Review the pre-configured agents: Sales VP, Marketing Director, CS Lead, and Product Manager. Each has unique personality traits that affect the simulation.',
    actionLabel: 'Continue with defaults',
    route: null,
    estimatedSeconds: 15,
  },
  {
    id: 'start-simulation',
    title: 'Start Simulation',
    narration: 'Launch the OASIS simulation. The agents will converse for multiple rounds, debating priorities and forming opinions about the pipeline.',
    actionLabel: 'Start Simulation',
    route: null,
    estimatedSeconds: 5,
  },
  {
    id: 'watch-messages',
    title: 'Watch Messages Flow',
    narration: 'Observe the agents interacting in real-time. Notice how sentiment shifts and coalitions form as rounds progress.',
    actionLabel: null,
    route: null,
    estimatedSeconds: 30,
  },
  {
    id: 'review-results',
    title: 'Review Results',
    narration: 'The simulation is complete. Explore the sentiment timeline, influence network, and coalition graph in the workspace.',
    actionLabel: 'View Results',
    route: null,
    estimatedSeconds: 20,
  },
  {
    id: 'generate-report',
    title: 'Generate Report',
    narration: 'Generate an AI-powered report that summarizes key findings, strategic recommendations, and stakeholder alignment insights.',
    actionLabel: 'Generate Report',
    route: null,
    estimatedSeconds: 15,
  },
]

/**
 * Keyboard shortcuts — organized by context.
 */
export const keyboardShortcuts = {
  global: [
    { keys: ['Ctrl', '/'], mac: ['Cmd', '/'], label: 'Toggle shortcut reference' },
    { keys: ['Ctrl', 'K'], mac: ['Cmd', 'K'], label: 'Quick search' },
    { keys: ['?'], mac: ['?'], label: 'Start welcome tour' },
  ],
  simulation: [
    { keys: ['Space'], mac: ['Space'], label: 'Pause / resume simulation' },
    { keys: ['Ctrl', 'Enter'], mac: ['Cmd', 'Enter'], label: 'Start simulation' },
    { keys: ['Esc'], mac: ['Esc'], label: 'Stop simulation' },
  ],
  workspace: [
    { keys: ['1'], mac: ['1'], label: 'Switch to Graph tab' },
    { keys: ['2'], mac: ['2'], label: 'Switch to Simulation tab' },
    { keys: ['3'], mac: ['3'], label: 'Switch to Report tab' },
    { keys: ['Tab'], mac: ['Tab'], label: 'Next panel' },
  ],
  navigation: [
    { keys: ['G', 'H'], mac: ['G', 'H'], label: 'Go to Home' },
    { keys: ['G', 'S'], mac: ['G', 'S'], label: 'Go to Simulations' },
    { keys: ['G', 'T'], mac: ['G', 'T'], label: 'Go to Settings' },
  ],
}
