/**
 * Contextual help entries for complex features.
 * Each entry: { id, title, description, learnMoreUrl? }
 */
export const helpEntries = {
  'oasis-simulation': {
    id: 'oasis-simulation',
    title: 'OASIS Simulation',
    description:
      'OASIS (Opinion-Aware Social Intelligence Simulation) models how GTM stakeholders interact, form opinions, and influence each other through multi-round agent conversations.',
  },
  'knowledge-graph': {
    id: 'knowledge-graph',
    title: 'Zep Knowledge Graph',
    description:
      'The knowledge graph extracts entities and relationships from your seed data, building a structured map that agents use to ground their conversations in real context.',
  },
  'personality-dynamics': {
    id: 'personality-dynamics',
    title: 'Personality Dynamics',
    description:
      'Each agent has personality traits (openness, assertiveness, risk tolerance) that influence how they respond to proposals, form alliances, and shift opinions over time.',
  },
  'coalition-detection': {
    id: 'coalition-detection',
    title: 'Coalition Detection',
    description:
      'The system identifies clusters of agents that align on positions during simulation — revealing which stakeholder groups naturally form alliances or opposition blocs.',
  },
  'what-if-analysis': {
    id: 'what-if-analysis',
    title: 'What-If Analysis',
    description:
      'Rerun simulations with modified parameters (different agents, changed personalities, new constraints) to compare outcomes and find optimal GTM strategies.',
  },
  'scenario-branching': {
    id: 'scenario-branching',
    title: 'Scenario Branching',
    description:
      'Fork a simulation at any round to explore alternative paths — useful for testing how different decisions at key moments change the final outcome.',
  },
  'd3-visualizations': {
    id: 'd3-visualizations',
    title: 'D3 Visualizations',
    description:
      'Interactive D3.js charts show sentiment timelines, influence networks, coalition graphs, and opinion distributions across simulation rounds.',
  },
}

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
