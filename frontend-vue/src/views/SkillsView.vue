<template>
  <div class="skills-container">
    <div class="skills-header">
      <div class="header-row">
        <button @click="goBack" class="back-btn">
          <span>←</span> 返回
        </button>
        <h1>🛠️ Skills 管理</h1>
      </div>
      <p class="subtitle">管理 AI 技能扩展</p>
    </div>

    <div class="skills-actions">
      <button @click="showImportModal = true" class="action-btn primary">
        📥 导入 Skill
      </button>
      <button @click="showCreateModal = true" class="action-btn">
        ✨ AI 创建 Skill
      </button>
    </div>

    <div class="skills-stats">
      <div class="stat-card">
        <div class="stat-value">{{ skills.length }}</div>
        <div class="stat-label">总 Skills</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ enabledCount }}</div>
        <div class="stat-label">已启用</div>
      </div>
    </div>

    <div class="skills-list">
      <div
        v-for="skill in skills"
        :key="skill.id"
        class="skill-item"
        :class="{ disabled: !skill.is_enabled }"
      >
        <div class="skill-main">
          <div class="skill-info">
            <div class="skill-name">{{ skill.name }}</div>
            <div class="skill-description">{{ skill.description }}</div>
            <div class="skill-meta">
              <span class="skill-date">创建: {{ formatDate(skill.created_at) }}</span>
            </div>
          </div>

          <div class="skill-actions">
            <button
              @click="toggleSkill(skill)"
              class="toggle-btn"
              :class="{ enabled: skill.is_enabled }"
            >
              {{ skill.is_enabled ? '禁用' : '启用' }}
            </button>
            <button @click="previewSkill(skill)" class="preview-btn">
              预览
            </button>
            <button @click="deleteSkill(skill)" class="delete-btn">
              删除
            </button>
          </div>
        </div>
      </div>

      <div v-if="skills.length === 0 && !loading" class="empty-state">
        <p>暂无已导入的 Skills</p>
        <p class="hint">点击上方按钮导入或创建新 Skill</p>
      </div>
    </div>

    <!-- 导入 Modal -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2>导入 Skill</h2>
          <button @click="showImportModal = false" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <p class="upload-hint">支持以下方式导入：</p>
          <ul class="upload-options">
            <li>📁 <strong>文件夹</strong> - 选择包含 SKILL.md 的文件夹</li>
            <li>📦 <strong>ZIP 文件</strong> - 包含 SKILL.md 的压缩包</li>
            <li>📄 <strong>单个 MD 文件</strong> - 仅 SKILL.md 文件</li>
          </ul>

          <div class="upload-area" @click="triggerFileInput">
            <input
              ref="fileInput"
              type="file"
              @change="handleFileUpload"
              accept=".md,.zip"
              style="display: none"
            />
            <div class="upload-icon">📁</div>
            <p>点击选择文件或拖拽到此处</p>
          </div>

          <div v-if="uploadStatus" class="upload-status" :class="uploadStatus.type">
            {{ uploadStatus.message }}
          </div>
        </div>
      </div>
    </div>

    <!-- 创建 Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeCreateModal">
      <div class="modal large">
        <div class="modal-header">
          <h2>✨ AI 创建 Skill</h2>
          <button @click="closeCreateModal" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Skill 名称</label>
            <input
              v-model="newSkill.name"
              type="text"
              placeholder="例如：代码优化助手"
            />
          </div>

          <div class="form-group">
            <label>功能描述</label>
            <textarea
              v-model="newSkill.description"
              placeholder="详细描述这个 Skill 的功能..."
              rows="3"
            ></textarea>
          </div>

          <div class="form-group">
            <label>具体要求（可选）</label>
            <textarea
              v-model="newSkill.requirements"
              placeholder="描述你希望这个 Skill 如何工作..."
              rows="4"
            ></textarea>
          </div>

          <div class="form-actions">
            <button @click="closeCreateModal" class="cancel-btn">取消</button>
            <button @click="createSkill" class="create-btn" :disabled="creating || !newSkill.name">
              {{ creating ? '创建中...' : '创建 Skill' }}
            </button>
          </div>

          <div v-if="createStatus" class="create-status" :class="createStatus.type">
            {{ createStatus.message }}
          </div>
        </div>
      </div>
    </div>

    <!-- 预览 Modal -->
    <div v-if="previewingSkill" class="modal-overlay" @click.self="previewingSkill = null">
      <div class="modal large">
        <div class="modal-header">
          <h2>{{ previewingSkill.name }}</h2>
          <button @click="previewingSkill = null" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <pre class="skill-content">{{ previewingSkill.content }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { buildApiUrl } from '../config/apiBase'

const router = useRouter()

function getAuthHeaders() {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

const loading = ref(false)
const skills = ref([])
const showImportModal = ref(false)
const showCreateModal = ref(false)
const previewingSkill = ref(null)
const creating = ref(false)
const uploadStatus = ref(null)
const createStatus = ref(null)
const fileInput = ref(null)

const newSkill = ref({
  name: '',
  description: '',
  requirements: ''
})

const enabledCount = computed(() => {
  return skills.value.filter(s => s.is_enabled).length
})

function goBack() {
  router.push('/chat')
}

async function fetchSkills() {
  try {
    loading.value = true
    const response = await axios.get(buildApiUrl('/skills'), { headers: getAuthHeaders() })
    skills.value = response.data.skills || []
  } catch (error) {
    console.error('[Skills] Failed to fetch:', error)
  } finally {
    loading.value = false
  }
}

async function toggleSkill(skill) {
  try {
    const response = await axios.post(buildApiUrl(`/skills/${skill.id}/toggle`), {}, { headers: getAuthHeaders() })
    const index = skills.value.findIndex(s => s.id === skill.id)
    if (index !== -1) {
      skills.value[index].is_enabled = response.data.is_enabled
    }
  } catch (error) {
    console.error('[Skills] Toggle failed:', error)
  }
}

async function deleteSkill(skill) {
  if (!confirm(`确定要删除 Skill "${skill.name}" 吗？`)) return

  try {
    await axios.delete(buildApiUrl(`/skills/${skill.id}`), { headers: getAuthHeaders() })
    skills.value = skills.value.filter(s => s.id !== skill.id)
  } catch (error) {
    console.error('[Skills] Delete failed:', error)
    alert('删除失败')
  }
}

async function previewSkill(skill) {
  try {
    const response = await axios.get(buildApiUrl(`/skills/${skill.id}/content`), { headers: getAuthHeaders() })
    previewingSkill.value = response.data
  } catch (error) {
    console.error('[Skills] Preview failed:', error)
  }
}

function triggerFileInput() {
  fileInput.value?.click()
}

async function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  try {
    uploadStatus.value = { type: 'info', message: '上传中...' }
    const response = await axios.post(buildApiUrl('/skills'), formData, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' }
    })

    uploadStatus.value = { type: 'success', message: response.data.message }
    await fetchSkills()

    setTimeout(() => {
      showImportModal.value = false
      uploadStatus.value = null
    }, 1500)
  } catch (error) {
    const message = error.response?.data?.detail || '上传失败'
    uploadStatus.value = { type: 'error', message }
  }
}

async function createSkill() {
  if (!newSkill.value.name) return

  creating.value = true
  createStatus.value = null

  try {
    const prompt = `创建一个名为 "${newSkill.value.name}" 的 Skill。

描述：${newSkill.value.description || '无'}

具体要求：${newSkill.value.requirements || '无'}

请生成一个完整的 SKILL.md 文件内容，包括：
1. Frontmatter（name, description）
2. Overview（功能概述）
3. Usage（使用方法）
4. Examples（使用示例）

请以 Markdown 格式返回。`

    const response = await axios.post(buildApiUrl('/skills/create'), {
      name: newSkill.value.name,
      description: newSkill.value.description,
      prompt: prompt
    }, { headers: getAuthHeaders() })

    createStatus.value = { type: 'success', message: response.data.message }
    await fetchSkills()

    setTimeout(() => {
      closeCreateModal()
    }, 1500)
  } catch (error) {
    const message = error.response?.data?.detail || '创建失败'
    createStatus.value = { type: 'error', message }
  } finally {
    creating.value = false
  }
}

function closeCreateModal() {
  showCreateModal.value = false
  newSkill.value = { name: '', description: '', requirements: '' }
  createStatus.value = null
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  fetchSkills()
})
</script>

<style scoped>
.skills-container {
  width: 100%;
  height: 100%;
  padding: var(--space-xl);
  overflow-y: auto;
  background: var(--bg-primary);
}

.skills-header {
  margin-bottom: var(--space-xl);
}

.header-row {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  color: var(--text-primary);
  border-color: var(--primary);
}

.skills-header h1 {
  font-size: 1.75rem;
  color: var(--text-primary);
}

.subtitle {
  color: var(--text-secondary);
}

.skills-actions {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.action-btn {
  padding: var(--space-sm) var(--space-lg);
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  border-color: var(--primary);
}

.action-btn.primary {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.action-btn.primary:hover {
  background: var(--primary-hover);
}

.skills-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.stat-card {
  padding: var(--space-lg);
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  text-align: center;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary);
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.skills-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.skill-item {
  padding: var(--space-lg);
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  transition: all 0.2s;
}

.skill-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.skill-item.disabled {
  opacity: 0.6;
}

.skill-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-lg);
}

.skill-info {
  flex: 1;
}

.skill-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-xs);
}

.skill-description {
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

.skill-meta {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.skill-actions {
  display: flex;
  gap: var(--space-sm);
}

.toggle-btn,
.preview-btn,
.delete-btn {
  padding: var(--space-xs) var(--space-sm);
  font-size: 0.875rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn {
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.toggle-btn.enabled {
  background: rgba(34, 197, 94, 0.15);
  border-color: #22c55e;
  color: #22c55e;
}

.preview-btn {
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid #3b82f6;
  color: #3b82f6;
}

.delete-btn {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid #ef4444;
  color: #ef4444;
}

.empty-state {
  text-align: center;
  padding: var(--space-2xl);
  color: var(--text-secondary);
}

.empty-state .hint {
  font-size: 0.875rem;
  color: var(--text-tertiary);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: hidden;
}

.modal.large {
  max-width: 700px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-lg);
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  font-size: 1.25rem;
  color: var(--text-primary);
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius-sm);
}

.close-btn:hover {
  background: var(--bg-elevated);
}

.modal-body {
  padding: var(--space-lg);
  overflow-y: auto;
  max-height: calc(80vh - 70px);
}

.upload-hint {
  margin-bottom: var(--space-md);
  color: var(--text-secondary);
}

.upload-options {
  margin-bottom: var(--space-lg);
  padding-left: var(--space-lg);
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.upload-options li {
  margin-bottom: var(--space-xs);
}

.upload-area {
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--space-2xl);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-area:hover {
  border-color: var(--primary);
  background: var(--bg-elevated);
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: var(--space-md);
}

.upload-area p {
  color: var(--text-secondary);
}

.upload-status {
  margin-top: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  text-align: center;
  font-size: 0.875rem;
}

.upload-status.success {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.upload-status.error {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.upload-status.info {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

/* Form */
.form-group {
  margin-bottom: var(--space-lg);
}

.form-group label {
  display: block;
  margin-bottom: var(--space-xs);
  font-weight: 500;
  color: var(--text-primary);
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  font-size: 1rem;
  color: var(--text-primary);
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  outline: none;
}

.form-group input:focus,
.form-group textarea:focus {
  border-color: var(--primary);
}

.form-group textarea {
  resize: vertical;
  font-family: inherit;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
  margin-top: var(--space-lg);
}

.cancel-btn {
  padding: var(--space-sm) var(--space-lg);
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
}

.create-btn {
  padding: var(--space-sm) var(--space-lg);
  background: var(--primary);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  cursor: pointer;
}

.create-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.create-status {
  margin-top: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  text-align: center;
  font-size: 0.875rem;
}

.create-status.success {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.create-status.error {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

/* Preview */
.skill-content {
  background: var(--bg-elevated);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 400px;
  overflow-y: auto;
}
</style>
