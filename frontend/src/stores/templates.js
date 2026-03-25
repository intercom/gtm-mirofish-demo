import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { templatesApi } from '../api/templates'

export const useTemplatesStore = defineStore('templates', () => {
  const templates = ref([])
  const categories = ref([])
  const loading = ref(false)
  const error = ref(null)
  const detailCache = ref({})

  const hasTemplates = computed(() => templates.value.length > 0)

  async function fetchTemplates({ category, tag, search } = {}, force = false) {
    if (templates.value.length > 0 && !force && !category && !tag && !search) {
      return templates.value
    }

    loading.value = true
    error.value = null
    try {
      const res = await templatesApi.list({ category, tag, search })
      templates.value = res.data.templates || []
      return templates.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchTemplate(id, force = false) {
    if (detailCache.value[id] && !force) return detailCache.value[id]

    loading.value = true
    error.value = null
    try {
      const res = await templatesApi.get(id)
      detailCache.value[id] = res.data
      return res.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function createTemplate(data) {
    loading.value = true
    error.value = null
    try {
      const res = await templatesApi.create(data)
      templates.value = []
      return res.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateTemplate(id, data) {
    loading.value = true
    error.value = null
    try {
      const res = await templatesApi.update(id, data)
      delete detailCache.value[id]
      templates.value = []
      return res.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function deleteTemplate(id) {
    loading.value = true
    error.value = null
    try {
      await templatesApi.remove(id)
      delete detailCache.value[id]
      templates.value = templates.value.filter((t) => t.id !== id)
      return true
    } catch (e) {
      error.value = e.message
      return false
    } finally {
      loading.value = false
    }
  }

  async function useTemplate(id) {
    try {
      await templatesApi.use(id)
    } catch {
      // non-critical — don't block the user
    }
  }

  async function rateTemplate(id, rating) {
    try {
      const res = await templatesApi.rate(id, rating)
      if (detailCache.value[id]) {
        detailCache.value[id] = res.data
      }
      return res.data
    } catch (e) {
      error.value = e.message
      return null
    }
  }

  async function fetchCategories(force = false) {
    if (categories.value.length > 0 && !force) return categories.value

    try {
      const res = await templatesApi.categories()
      categories.value = res.data.categories || []
      return categories.value
    } catch (e) {
      error.value = e.message
      return []
    }
  }

  function clearCache() {
    templates.value = []
    categories.value = []
    detailCache.value = {}
    error.value = null
  }

  return {
    templates,
    categories,
    loading,
    error,
    detailCache,
    hasTemplates,
    fetchTemplates,
    fetchTemplate,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    useTemplate,
    rateTemplate,
    fetchCategories,
    clearCache,
  }
})
