import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import axios from 'axios'

export const usePlannerStore = defineStore('planner', () => {
  const plans = ref([])
  const currentPlanId = ref(null)
  const isLoading = ref(false)
  const isGenerating = ref(false)

  const currentPlan = computed(() => {
    return plans.value.find(plan => plan.id === currentPlanId.value) || plans.value[0] || null
  })

  function getAuthHeaders() {
    const token = localStorage.getItem('token')
    if (!token) {
      return {}
    }
    return {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }

  async function loadPlans({ conversationId = null } = {}) {
    isLoading.value = true
    try {
      const response = await axios.get('/api/plans', {
        params: conversationId ? { conversation_id: conversationId } : {},
        headers: getAuthHeaders()
      })
      plans.value = Array.isArray(response.data) ? response.data : []
      if (!plans.value.some(plan => plan.id === currentPlanId.value)) {
        currentPlanId.value = plans.value[0]?.id || null
      }
      return plans.value
    } finally {
      isLoading.value = false
    }
  }

  async function createPlan({ objective, conversationId = null, items = [] }) {
    const response = await axios.post('/api/plans', {
      objective,
      conversation_id: conversationId,
      source: 'manual',
      items
    }, {
      headers: getAuthHeaders()
    })
    upsertPlan(response.data, true)
    return response.data
  }

  async function generatePlan({ objective, conversationId = null }) {
    isGenerating.value = true
    try {
      const response = await axios.post('/api/plans/generate', {
        objective,
        conversation_id: conversationId,
        source: 'chat_generate'
      }, {
        headers: getAuthHeaders()
      })
      upsertPlan(response.data, true)
      return response.data
    } finally {
      isGenerating.value = false
    }
  }

  async function updatePlan(planId, payload) {
    const response = await axios.patch(`/api/plans/${planId}`, payload, {
      headers: getAuthHeaders()
    })
    upsertPlan(response.data)
    return response.data
  }

  async function addPlanItem(planId, payload) {
    const response = await axios.post(`/api/plans/${planId}/items`, payload, {
      headers: getAuthHeaders()
    })
    upsertPlan(response.data)
    return response.data
  }

  async function updatePlanItem(planId, itemId, payload) {
    const response = await axios.patch(`/api/plans/${planId}/items/${itemId}`, payload, {
      headers: getAuthHeaders()
    })
    upsertPlan(response.data)
    return response.data
  }

  async function deletePlanItem(planId, itemId) {
    const response = await axios.delete(`/api/plans/${planId}/items/${itemId}`, {
      headers: getAuthHeaders()
    })
    upsertPlan(response.data)
    return response.data
  }

  function setCurrentPlan(planId) {
    currentPlanId.value = planId
  }

  function upsertPlan(plan, makeCurrent = false) {
    const index = plans.value.findIndex(item => item.id === plan.id)
    if (index === -1) {
      plans.value.unshift(plan)
    } else {
      plans.value.splice(index, 1, plan)
    }
    if (makeCurrent || !currentPlanId.value) {
      currentPlanId.value = plan.id
    }
  }

  return {
    plans,
    currentPlanId,
    currentPlan,
    isLoading,
    isGenerating,
    loadPlans,
    createPlan,
    generatePlan,
    updatePlan,
    addPlanItem,
    updatePlanItem,
    deletePlanItem,
    setCurrentPlan,
    upsertPlan
  }
})
