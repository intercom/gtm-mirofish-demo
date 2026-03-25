import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'
import { agentsApi } from '../api/agents'

const STORAGE_KEY = 'mirofish_custom_agents'

const DEPARTMENTS = ['Sales', 'Marketing', 'CS', 'Product', 'Finance', 'Engineering', 'Executive']

const TEMPLATE_AGENTS = [
  {
    id: 'tmpl-vp-support',
    name: 'Jordan Rivera',
    role: 'VP of Customer Support',
    department: 'CS',
    personality: { analytical: 65, creative: 40, assertive: 80, empathetic: 70, risk_tolerant: 45 },
    expertise_areas: ['Customer Retention', 'Team Leadership', 'Support Operations', 'Vendor Evaluation'],
    communication_style: 'formal',
    biases: ['Status quo bias'],
    goals: ['Reduce ticket resolution time', 'Improve CSAT scores'],
    backstory: 'Manages a 50-person support team at a mid-market SaaS company. Currently evaluating AI-first support tools to reduce costs while improving customer satisfaction.',
    avatar_color: '#2068FF',
    is_template: true,
  },
  {
    id: 'tmpl-cx-director',
    name: 'Sarah Chen',
    role: 'CX Director',
    department: 'CS',
    personality: { analytical: 75, creative: 55, assertive: 60, empathetic: 85, risk_tolerant: 50 },
    expertise_areas: ['Customer Experience', 'Data Analytics', 'Journey Mapping', 'NPS Programs'],
    communication_style: 'data_driven',
    biases: ['Confirmation bias'],
    goals: ['Unify customer touchpoints', 'Drive NPS above 50'],
    backstory: 'Leads CX strategy at a B2B enterprise. Obsessed with measuring every customer interaction and building data-driven playbooks.',
    avatar_color: '#ff5600',
    is_template: true,
  },
  {
    id: 'tmpl-it-leader',
    name: 'Marcus Thompson',
    role: 'IT Director',
    department: 'Engineering',
    personality: { analytical: 90, creative: 30, assertive: 55, empathetic: 35, risk_tolerant: 25 },
    expertise_areas: ['Security & Compliance', 'System Integration', 'API Architecture', 'Vendor Assessment'],
    communication_style: 'formal',
    biases: ['Status quo bias', 'Anchoring'],
    goals: ['Ensure SOC2 compliance', 'Minimize integration complexity'],
    backstory: 'Responsible for all SaaS tool procurement and integration at a 500-person company. Skeptical of marketing claims and focused on security certifications.',
    avatar_color: '#AA00FF',
    is_template: true,
  },
  {
    id: 'tmpl-rev-ops',
    name: 'Priya Patel',
    role: 'Revenue Operations Manager',
    department: 'Sales',
    personality: { analytical: 80, creative: 45, assertive: 50, empathetic: 55, risk_tolerant: 40 },
    expertise_areas: ['Revenue Operations', 'Pipeline Management', 'Forecasting', 'CRM Administration'],
    communication_style: 'data_driven',
    biases: ['Recency bias'],
    goals: ['Improve pipeline accuracy', 'Reduce sales cycle length'],
    backstory: 'Runs the revenue engine at a Series C startup. Lives in Salesforce dashboards and always has pipeline metrics at her fingertips.',
    avatar_color: '#009900',
    is_template: true,
  },
  {
    id: 'tmpl-cmo',
    name: 'Alex Kim',
    role: 'Chief Marketing Officer',
    department: 'Executive',
    personality: { analytical: 55, creative: 85, assertive: 75, empathetic: 60, risk_tolerant: 70 },
    expertise_areas: ['Growth Marketing', 'Brand Strategy', 'Demand Generation', 'Content Marketing'],
    communication_style: 'storytelling',
    biases: ['Optimism bias'],
    goals: ['Double MQLs this quarter', 'Launch competitive positioning campaign'],
    backstory: 'Visionary marketer who built the marketing function from scratch at two successful startups. Believes in bold bets and category creation.',
    avatar_color: '#FFB800',
    is_template: true,
  },
  {
    id: 'tmpl-cfo',
    name: 'Diana Okafor',
    role: 'CFO',
    department: 'Finance',
    personality: { analytical: 95, creative: 20, assertive: 70, empathetic: 40, risk_tolerant: 15 },
    expertise_areas: ['Financial Planning', 'Budget Allocation', 'ROI Analysis', 'Vendor Contracts'],
    communication_style: 'formal',
    biases: ['Anchoring', 'Status quo bias'],
    goals: ['Reduce SaaS spend by 15%', 'Improve cost per resolution'],
    backstory: 'Finance executive who scrutinizes every dollar spent on software. Needs clear ROI justification and prefers annual contracts with exit clauses.',
    avatar_color: '#E0245E',
    is_template: true,
  },
]

function loadStoredAgents() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export const useAgentsStore = defineStore('agents', () => {
  const agents = ref(loadStoredAgents())
  const loading = ref(false)
  const error = ref(null)

  watch(agents, (val) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(val))
    } catch {
      // Storage full — silently ignore
    }
  }, { deep: true })

  const templates = computed(() => TEMPLATE_AGENTS)
  const hasAgents = computed(() => agents.value.length > 0)

  const allDepartments = computed(() => {
    const depts = new Set(DEPARTMENTS)
    for (const a of agents.value) {
      if (a.department) depts.add(a.department)
    }
    return [...depts].sort()
  })

  const allRoles = computed(() => {
    const roles = new Set()
    for (const a of [...agents.value, ...TEMPLATE_AGENTS]) {
      if (a.role) roles.add(a.role)
    }
    return [...roles].sort()
  })

  function addAgent(agent) {
    const entry = {
      ...agent,
      id: agent.id || `agent-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      created_at: agent.created_at || new Date().toISOString(),
      is_template: false,
    }
    agents.value.push(entry)
    return entry
  }

  function updateAgent(id, updates) {
    const idx = agents.value.findIndex(a => a.id === id)
    if (idx === -1) return null
    agents.value[idx] = { ...agents.value[idx], ...updates, updated_at: new Date().toISOString() }
    return agents.value[idx]
  }

  function removeAgent(id) {
    const idx = agents.value.findIndex(a => a.id === id)
    if (idx !== -1) agents.value.splice(idx, 1)
  }

  function cloneAgent(id) {
    const source = agents.value.find(a => a.id === id) || TEMPLATE_AGENTS.find(t => t.id === id)
    if (!source) return null
    const cloned = {
      ...JSON.parse(JSON.stringify(source)),
      id: `agent-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      name: `${source.name} (Copy)`,
      created_at: new Date().toISOString(),
      is_template: false,
    }
    agents.value.push(cloned)
    return cloned
  }

  function getAgent(id) {
    return agents.value.find(a => a.id === id) || TEMPLATE_AGENTS.find(t => t.id === id) || null
  }

  async function fetchAgents() {
    loading.value = true
    error.value = null
    try {
      const { data } = await agentsApi.list()
      if (data?.data && Array.isArray(data.data)) {
        agents.value = data.data
      }
    } catch {
      // Backend not available — use localStorage agents
    } finally {
      loading.value = false
    }
  }

  return {
    agents,
    templates,
    loading,
    error,
    hasAgents,
    allDepartments,
    allRoles,
    addAgent,
    updateAgent,
    removeAgent,
    cloneAgent,
    getAgent,
    fetchAgents,
  }
})
