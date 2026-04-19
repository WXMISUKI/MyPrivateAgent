import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const API_BASE_URL = '/api'

export const chatApi = {
  async sendMessage(message, conversationId = null) {
    const authStore = useAuthStore()

    const response = await axios.post(
      `${API_BASE_URL}/chat`,
      { message, conversation_id: conversationId },
      {
        headers: {
          Authorization: `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        },
        timeout: 300000
      }
    )

    return response.data
  },

  async regenerateMessage(messageIndex, conversationId = null) {
    const authStore = useAuthStore()

    const response = await axios.post(
      `${API_BASE_URL}/chat/regenerate`,
      { message_index: messageIndex, conversation_id: conversationId },
      {
        headers: {
          Authorization: `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        }
      }
    )

    return response.data
  },

  async abortStream() {
    const authStore = useAuthStore()

    await axios.post(
      `${API_BASE_URL}/chat/abort`,
      {},
      {
        headers: {
          Authorization: `Bearer ${authStore.token}`
        }
      }
    )
  },

  async getChatHistory(conversationId) {
    const authStore = useAuthStore()

    const response = await axios.get(`${API_BASE_URL}/chat/history/${conversationId}`, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    })

    return response.data
  }
}

export default chatApi
