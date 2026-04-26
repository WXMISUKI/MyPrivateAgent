import LZString from 'lz-string'

const STORAGE_KEY = 'myprivateagent_conversations'
const ACTIVE_KEY = 'myprivateagent_active_id'
const MAX_MESSAGES_PER_CONVERSATION = 100
const MAX_CONVERSATIONS = 50

export const storage = {
  saveConversations(conversations) {
    try {
      let dataToSave = conversations

      if (conversations.length > MAX_CONVERSATIONS) {
        dataToSave = conversations.slice(0, MAX_CONVERSATIONS)
        console.log('[Storage] Truncated conversations to', MAX_CONVERSATIONS)
      }

      const jsonStr = JSON.stringify(dataToSave)
      const compressed = LZString.compressToUTF16(jsonStr)

      const originalSize = new Blob([jsonStr]).size
      const compressedSize = new Blob([compressed]).size

      console.log('[Storage] Compressed:', originalSize, '->', compressedSize, 'bytes', Math.round((1 - compressedSize / originalSize) * 100), '% saved')

      localStorage.setItem(STORAGE_KEY, compressed)
    } catch (error) {
      console.error('[Storage] Failed to save conversations:', error)
      if (error.name === 'QuotaExceededError') {
        this.cleanupOldConversations()
        const jsonStr = JSON.stringify(conversations)
        const compressed = LZString.compressToUTF16(jsonStr)
        localStorage.setItem(STORAGE_KEY, compressed)
      }
    }
  },

  loadConversations() {
    try {
      const compressed = localStorage.getItem(STORAGE_KEY)
      if (!compressed) return []

      const decompressed = LZString.decompressFromUTF16(compressed)
      if (!decompressed) {
        const json = localStorage.getItem(STORAGE_KEY)
        return json ? JSON.parse(json) : []
      }

      const data = JSON.parse(decompressed)

      return data.map(conv => {
        if (conv.messages && conv.messages.length > MAX_MESSAGES_PER_CONVERSATION) {
          conv.messages = conv.messages.slice(-MAX_MESSAGES_PER_CONVERSATION)
          console.log('[Storage] Truncated messages in conversation', conv.id)
        }
        return conv
      })
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
  },

  cleanupOldConversations() {
    try {
      const conversations = this.loadConversations()
      if (conversations.length > MAX_CONVERSATIONS / 2) {
        const sorted = conversations.sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0))
        const toKeep = sorted.slice(0, Math.floor(MAX_CONVERSATIONS / 2))
        this.saveConversations(toKeep)
        console.log('[Storage] Cleaned up old conversations, kept', toKeep.length)
      }
    } catch (error) {
      console.error('[Storage] Failed to cleanup old conversations:', error)
    }
  },

  getStorageUsage() {
    try {
      const data = localStorage.getItem(STORAGE_KEY) || ''
      const size = new Blob([data]).size
      const maxSize = 5 * 1024 * 1024
      return {
        used: size,
        max: maxSize,
        percentage: Math.round((size / maxSize) * 100)
      }
    } catch (error) {
      return { used: 0, max: 0, percentage: 0 }
    }
  }
}

export default storage