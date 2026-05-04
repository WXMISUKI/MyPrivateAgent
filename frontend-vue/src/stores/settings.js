import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  const theme = ref(localStorage.getItem('theme') || 'dark')
  const defaultModel = ref(localStorage.getItem('defaultModel') || 'gpt-4')
  const temperature = ref(parseFloat(localStorage.getItem('temperature')) || 0.7)
  const maxContextLength = ref(parseInt(localStorage.getItem('maxContextLength')) || 8192)
  const autoSave = ref(localStorage.getItem('autoSave') !== 'false')
  const streamResponse = ref(localStorage.getItem('streamResponse') !== 'false')
  const showTokenCount = ref(localStorage.getItem('showTokenCount') !== 'false')
  const failoverMediumThreshold = ref(parseFloat(localStorage.getItem('failoverMediumThreshold')) || 0.2)
  const failoverHighThreshold = ref(parseFloat(localStorage.getItem('failoverHighThreshold')) || 0.4)
  const muteHealthAlerts = ref(localStorage.getItem('muteHealthAlerts') === 'true')

  function setTheme(value) {
    theme.value = value
    localStorage.setItem('theme', value)
    document.documentElement.setAttribute('data-theme', value)
  }

  function toggleTheme() {
    const newTheme = theme.value === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
  }

  function setDefaultModel(value) {
    defaultModel.value = value
    localStorage.setItem('defaultModel', value)
  }

  function setTemperature(value) {
    temperature.value = value
    localStorage.setItem('temperature', value.toString())
  }

  function setMaxContextLength(value) {
    maxContextLength.value = value
    localStorage.setItem('maxContextLength', value.toString())
  }

  function setAutoSave(value) {
    autoSave.value = value
    localStorage.setItem('autoSave', value.toString())
  }

  function setStreamResponse(value) {
    streamResponse.value = value
    localStorage.setItem('streamResponse', value.toString())
  }

  function setShowTokenCount(value) {
    showTokenCount.value = value
    localStorage.setItem('showTokenCount', value.toString())
  }

  function setFailoverMediumThreshold(value) {
    failoverMediumThreshold.value = value
    localStorage.setItem('failoverMediumThreshold', value.toString())
  }

  function setFailoverHighThreshold(value) {
    failoverHighThreshold.value = value
    localStorage.setItem('failoverHighThreshold', value.toString())
  }

  function setMuteHealthAlerts(value) {
    muteHealthAlerts.value = value
    localStorage.setItem('muteHealthAlerts', value.toString())
  }

  function getSettings() {
    return {
      theme: theme.value,
      defaultModel: defaultModel.value,
      temperature: temperature.value,
      maxContextLength: maxContextLength.value,
      autoSave: autoSave.value,
      streamResponse: streamResponse.value,
      showTokenCount: showTokenCount.value,
      failoverMediumThreshold: failoverMediumThreshold.value,
      failoverHighThreshold: failoverHighThreshold.value,
      muteHealthAlerts: muteHealthAlerts.value
    }
  }

  return {
    theme,
    defaultModel,
    temperature,
    maxContextLength,
    autoSave,
    streamResponse,
    showTokenCount,
    failoverMediumThreshold,
    failoverHighThreshold,
    muteHealthAlerts,
    setTheme,
    toggleTheme,
    setDefaultModel,
    setTemperature,
    setMaxContextLength,
    setAutoSave,
    setStreamResponse,
    setShowTokenCount,
    setFailoverMediumThreshold,
    setFailoverHighThreshold,
    setMuteHealthAlerts,
    getSettings
  }
})
