const STORAGE_KEY = 'myprivateagent_conversations'
const ACTIVE_KEY = 'myprivateagent_active_id'

export const storage = {
  saveConversations(conversations) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
    } catch (error) {
      console.error('[Storage] Failed to save conversations:', error)
    }
  },

  loadConversations() {
    try {
      const data = localStorage.getItem(STORAGE_KEY)
      return data ? JSON.parse(data) : []
    } catch (error) {
      console.error('[Storage] Failed to load conversations:', error)
      return []
    }
  },

  getActiveId() {
    try {
      return localStorage.getItem(ACTIVE_KEY)
    } catch (error) {
      console.error('[Storage] Failed to get active id:', error)
      return null
    }
  },

  setActiveId(id) {
    try {
      if (id) {
        localStorage.setItem(ACTIVE_KEY, String(id))
      } else {
        localStorage.removeItem(ACTIVE_KEY)
      }
    } catch (error) {
      console.error('[Storage] Failed to set active id:', error)
    }
  },

  clearAll() {
    try {
      localStorage.removeItem(STORAGE_KEY)
      localStorage.removeItem(ACTIVE_KEY)
    } catch (error) {
      console.error('[Storage] Failed to clear storage:', error)
    }
  },

  exportData() {
    return {
      conversations: this.loadConversations(),
      activeId: this.getActiveId(),
      exportedAt: new Date().toISOString()
    }
  },

  importData(data) {
    try {
      if (data.conversations) {
        this.saveConversations(data.conversations)
      }
      if (data.activeId) {
        this.setActiveId(data.activeId)
      }
      return true
    } catch (error) {
      console.error('[Storage] Failed to import data:', error)
      return false
    }
  }
}

export default storage
