import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import client from '../api/client'

export const useSalesforceStore = defineStore('salesforce', () => {
  const accounts = ref([])
  const opportunities = ref([])
  const contacts = ref([])
  const leads = ref([])
  const stats = ref({})
  const loading = ref(false)
  const error = ref(null)

  // --- Getters ---

  const accountsByIndustry = computed(() => {
    const grouped = {}
    for (const account of accounts.value) {
      const industry = account.industry || 'Unknown'
      if (!grouped[industry]) grouped[industry] = []
      grouped[industry].push(account)
    }
    return grouped
  })

  const opportunitiesByStage = computed(() => {
    const grouped = {}
    for (const opp of opportunities.value) {
      const stage = opp.stage || 'Unknown'
      if (!grouped[stage]) grouped[stage] = []
      grouped[stage].push(opp)
    }
    return grouped
  })

  const leadsByStatus = computed(() => {
    const grouped = {}
    for (const lead of leads.value) {
      const status = lead.status || 'Unknown'
      if (!grouped[status]) grouped[status] = []
      grouped[status].push(lead)
    }
    return grouped
  })

  const totalPipelineValue = computed(() =>
    opportunities.value.reduce((sum, opp) => sum + (opp.amount || 0), 0),
  )

  const avgHealthScore = computed(() => {
    if (accounts.value.length === 0) return 0
    const total = accounts.value.reduce((sum, a) => sum + (a.health_score || 0), 0)
    return total / accounts.value.length
  })

  // --- Actions ---

  async function fetchAccounts(filters = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await client.get('/salesforce/accounts', { params: filters })
      accounts.value = res.data.accounts || res.data || []
      return accounts.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchOpportunities(filters = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await client.get('/salesforce/opportunities', { params: filters })
      opportunities.value = res.data.opportunities || res.data || []
      return opportunities.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchContacts(accountId) {
    loading.value = true
    error.value = null
    try {
      const params = accountId ? { account_id: accountId } : {}
      const res = await client.get('/salesforce/contacts', { params })
      contacts.value = res.data.contacts || res.data || []
      return contacts.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchLeads(filters = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await client.get('/salesforce/leads', { params: filters })
      leads.value = res.data.leads || res.data || []
      return leads.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    loading.value = true
    error.value = null
    try {
      const res = await client.get('/salesforce/stats')
      stats.value = res.data || {}
      return stats.value
    } catch (e) {
      error.value = e.message
      return {}
    } finally {
      loading.value = false
    }
  }

  return {
    accounts,
    opportunities,
    contacts,
    leads,
    stats,
    loading,
    error,
    accountsByIndustry,
    opportunitiesByStage,
    leadsByStatus,
    totalPipelineValue,
    avgHealthScore,
    fetchAccounts,
    fetchOpportunities,
    fetchContacts,
    fetchLeads,
    fetchStats,
  }
})
