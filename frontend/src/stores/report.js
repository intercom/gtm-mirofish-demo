import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useReportStore = defineStore('report', () => {
  const selectedTemplate = ref(null)
  const reportId = ref(null)
  const templateId = ref(null)

  const hasTemplate = computed(() => !!selectedTemplate.value)

  const isAIPlanned = computed(
    () => !selectedTemplate.value || selectedTemplate.value.section_count === 0,
  )

  function setTemplate(tpl) {
    selectedTemplate.value = tpl
    templateId.value = tpl?.id || null
  }

  function setReportId(id) {
    reportId.value = id
  }

  function reset() {
    selectedTemplate.value = null
    reportId.value = null
    templateId.value = null
  }

  return {
    selectedTemplate,
    reportId,
    templateId,
    hasTemplate,
    isAIPlanned,
    setTemplate,
    setReportId,
    reset,
  }
})
