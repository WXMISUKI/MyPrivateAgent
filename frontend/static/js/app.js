// 主应用 JavaScript

const API_BASE = '';

// 全局状态
let currentUser = null;
let currentConversationId = null;
let conversations = [];
let isGenerating = false;  // AI是否正在生成
let abortController = null;  // 用于中断请求
let lastUserMessageId = null;  // 最后一条用户消息的ID（用于中断时删除）

// ============ Markdown 渲染配置 ============
if (typeof marked !== 'undefined') {
    marked.setOptions({
        breaks: true,  // 允许换行
        gfm: true      // GitHub风格Markdown
    });
}

// 渲染消息内容（支持Markdown）
function renderMessageContent(content) {
    if (typeof marked !== 'undefined') {
        try {
            return marked.parse(content);
        } catch (e) {
            console.warn('Markdown解析失败:', e);
            return content.replace(/\n/g, '<br>');
        }
    }
    // 如果没有marked库，直接换行
    return content.replace(/\n/g, '<br>');
}

// DOM 元素
const elements = {
    userButton: document.getElementById('user-button'),
    userDropdown: document.getElementById('user-dropdown'),
    logoutBtn: document.getElementById('logout-btn'),
    newChatBtn: document.getElementById('new-chat-btn'),
    conversationList: document.getElementById('conversation-list'),
    modelSelect: document.getElementById('model-select'),
    messagesContainer: document.getElementById('messages-container'),
    welcomeMessage: document.getElementById('welcome-message'),
    messageInput: document.getElementById('message-input'),
    sendButton: document.getElementById('send-button'),
    currentUsername: document.getElementById('current-username'),
    // Skills 相关
    skillsButton: document.getElementById('skills-button'),
    skillsCount: document.getElementById('skills-count'),
    skillsModal: document.getElementById('skills-modal'),
    skillsClose: document.getElementById('skills-close'),
    skillsStats: document.getElementById('skills-stats'),
    skillsTotal: document.getElementById('skills-total'),
    skillsEnabled: document.getElementById('skills-enabled'),
    skillsList: document.getElementById('skills-list'),
    importSkillFolderBtn: document.getElementById('import-skill-folder-btn'),
    importSkillBtn: document.getElementById('import-skill-btn'),
    skillFolderInput: document.getElementById('skill-folder-input'),
    skillFileInput: document.getElementById('skill-file-input')
};

function getAuthHeader() {
    const token = localStorage.getItem('access_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    await checkAuth();
    await loadUserInfo();
    await loadConversations();
    await loadSkills();  // 加载Skills

    // 绑定事件
    bindEvents();
});

async function checkAuth() {
    const token = localStorage.getItem('access_token');
    console.log('[checkAuth] Token:', token ? '存在' : '不存在');
    console.log('[checkAuth] Token值:', token);

    if (!token) {
        window.location.href = '/login';
        return;
    }

    try {
        const headers = getAuthHeader();
        console.log('[checkAuth] 请求头:', headers);

        const response = await fetch('/api/auth/me', {
            headers: headers
        });
        console.log('[checkAuth] 响应状态:', response.status);

        if (!response.ok) {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
            return;
        }
        currentUser = await response.json();
        console.log('[checkAuth] 用户信息:', currentUser);
    } catch (e) {
        console.error('[checkAuth] 错误:', e);
        localStorage.removeItem('access_token');
        window.location.href = '/login';
    }
}

async function loadUserInfo() {
    elements.currentUsername.textContent = currentUser.username;
}

async function loadConversations() {
    try {
        const response = await fetch('/api/conversations', {
            headers: getAuthHeader()
        });
        if (response.ok) {
            conversations = await response.json();
            renderConversationList();
        }
    } catch (e) {
        console.error('加载会话失败:', e);
    }
}

function renderConversationList() {
    elements.conversationList.innerHTML = '';

    if (conversations.length === 0) {
        elements.conversationList.innerHTML = '<div class="empty-list">暂无对话记录</div>';
        return;
    }

    conversations.forEach(conv => {
        const item = document.createElement('div');
        item.className = `conversation-item${conv.id === currentConversationId ? ' active' : ''}`;
        item.innerHTML = `
            <span class="title">${conv.title}</span>
            <button class="delete-btn" data-id="${conv.id}" title="删除对话">🗑️</button>
        `;
        item.addEventListener('click', (e) => {
            if (!e.target.classList.contains('delete-btn')) {
                selectConversation(conv.id);
            }
        });
        elements.conversationList.appendChild(item);
    });

    // 绑定删除事件
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const id = parseInt(btn.dataset.id);
            await deleteConversation(id);
        });
    });
}

async function selectConversation(id) {
    currentConversationId = id;
    renderConversationList();

    try {
        const response = await fetch(`/api/conversations/${id}`, {
            headers: getAuthHeader()
        });
        if (response.ok) {
            const data = await response.json();
            elements.welcomeMessage.style.display = 'none';
            elements.modelSelect.value = data.model_name;
            renderMessages(data.messages);
        }
    } catch (e) {
        console.error('加载会话详情失败:', e);
    }
}

function renderMessages(messages) {
    elements.messagesContainer.innerHTML = '';

    messages.forEach(msg => {
        appendMessage(msg.role, msg.content);
    });

    scrollToBottom();
}

function appendMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    // AI消息使用Markdown渲染，用户消息直接显示
    const htmlContent = role === 'assistant' ? renderMessageContent(content) : content.replace(/\n/g, '<br>');
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${role === 'user' ? '👤' : '🤖'}</div>
        <div class="message-content">${htmlContent}</div>
    `;
    elements.messagesContainer.appendChild(messageDiv);
}

function appendLoadingIndicator() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant';
    loadingDiv.id = 'loading-indicator';
    loadingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="thinking-indicator">
            <span>🤔 AI正在思考</span>
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    elements.messagesContainer.appendChild(loadingDiv);
    scrollToBottom();
}

function removeLoadingIndicator() {
    const loading = document.getElementById('loading-indicator');
    if (loading) {
        loading.remove();
    }
}

function scrollToBottom() {
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
}

// 设置输入区域状态
function setInputState(generating) {
    isGenerating = generating;
    elements.messageInput.disabled = generating;
    elements.sendButton.disabled = false;  // 暂停按钮始终可用
    elements.sendButton.classList.toggle('generating', generating);
    elements.sendButton.textContent = generating ? '暂停' : '发送';
}

function bindEvents() {
    // 用户菜单
    elements.userButton.addEventListener('click', () => {
        elements.userDropdown.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
        if (!elements.userButton.contains(e.target)) {
            elements.userDropdown.classList.remove('show');
        }
    });

    // 退出登录
    elements.logoutBtn.addEventListener('click', handleLogout);

    // 新建对话
    elements.newChatBtn.addEventListener('click', createNewConversation);

    // 发送消息
    elements.sendButton.addEventListener('click', sendMessage);

    // 输入框回车发送
    elements.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 调整输入框高度
    elements.messageInput.addEventListener('input', () => {
        elements.messageInput.style.height = 'auto';
        elements.messageInput.style.height = Math.min(elements.messageInput.scrollHeight, 120) + 'px';
    });

    // 模型切换
    if (elements.modelSelect) {
        elements.modelSelect.addEventListener('change', handleModelChange);
    }
    
    // Skills 相关事件
    if (elements.skillsButton) {
        console.log('[Skills] skillsButton 元素找到');
        elements.skillsButton.addEventListener('click', () => {
            console.log('[Skills] 点击了 skillsButton');
            // 直接获取 modal 元素
            const modalEl = document.getElementById('skills-modal');
            if (modalEl) {
                console.log('[Skills] 添加 show 类到 modal');
                modalEl.classList.add('show');
            }
            loadSkillsList();
        });
    } else {
        console.log('[Skills] skillsButton 元素未找到');
    }
    
    // 关闭按钮
    document.addEventListener('click', function(e) {
        if (e.target && e.target.id === 'skills-close') {
            const modalEl = document.getElementById('skills-modal');
            if (modalEl) {
                modalEl.classList.remove('show');
            }
        }
    });
    
    // 点击遮罩关闭
    document.addEventListener('click', function(e) {
        const modalEl = document.getElementById('skills-modal');
        if (e.target === modalEl) {
            modalEl.classList.remove('show');
        }
    });
    
    // 导入 Skill 按钮（文件夹方式 - 推荐）
    const importFolderBtn = document.getElementById('import-skill-folder-btn');
    if (importFolderBtn) {
        importFolderBtn.addEventListener('click', function() {
            const folderInput = document.getElementById('skill-folder-input');
            if (folderInput) {
                folderInput.click();
            }
        });
    }
    
    // 导入 Skill 按钮（ZIP/MD文件方式）
    const importFileBtn = document.getElementById('import-skill-btn');
    if (importFileBtn) {
        importFileBtn.addEventListener('click', function() {
            const fileInput = document.getElementById('skill-file-input');
            if (fileInput) {
                fileInput.click();
            }
        });
    }
    
    // 文件夹选择
    const folderInput = document.getElementById('skill-folder-input');
    if (folderInput) {
        folderInput.addEventListener('change', handleSkillFolderSelect);
    }
    
    // 文件选择（ZIP/MD）
    const fileInput = document.getElementById('skill-file-input');
    if (fileInput) {
        fileInput.addEventListener('change', handleSkillFileSelect);
    }
}

async function handleLogout() {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
}

async function handleModelChange() {
    if (!currentConversationId) return;

    const modelName = elements.modelSelect.value;
    const conversation = conversations.find(c => c.id === currentConversationId);
    if (!conversation) return;

    // 如果模型没变，不更新
    if (conversation.model_name === modelName) return;

    try {
        const response = await fetch(`/api/conversations/${currentConversationId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            },
            body: JSON.stringify({ model_name: modelName })
        });

        if (response.ok) {
            conversation.model_name = modelName;
            console.log('模型已切换:', modelName);
        }
    } catch (e) {
        console.error('切换模型失败:', e);
    }
}

async function createNewConversation() {
    const modelName = elements.modelSelect.value;

    try {
        const response = await fetch('/api/conversations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            },
            body: JSON.stringify({
                title: '新对话',
                model_name: modelName
            })
        });

        if (response.ok) {
            const conv = await response.json();
            conversations.unshift(conv);
            currentConversationId = conv.id;
            renderConversationList();

            // 清空消息显示
            elements.messagesContainer.innerHTML = '';
            elements.welcomeMessage.style.display = 'none';
        }
    } catch (e) {
        console.error('创建会话失败:', e);
    }
}

async function deleteConversation(id) {
    if (!confirm('确定要删除这个对话吗？')) {
        return;
    }

    try {
        const response = await fetch(`/api/conversations/${id}`, {
            method: 'DELETE',
            headers: getAuthHeader()
        });

        if (response.ok) {
            conversations = conversations.filter(c => c.id !== id);

            if (currentConversationId === id) {
                currentConversationId = null;
                elements.messagesContainer.innerHTML = '';
                elements.welcomeMessage.style.display = 'block';
            }

            renderConversationList();
        }
    } catch (e) {
        console.error('删除会话失败:', e);
    }
}

async function sendMessage() {
    // 如果AI正在生成，点击按钮表示中断
    if (isGenerating) {
        console.log('[Chat] 用户中断对话');
        if (abortController) {
            abortController.abort();
        }
        // 删除本次对话内容
        await handleAbort();
        return;
    }

    const message = elements.messageInput.value.trim();
    if (!message) return;

    if (!currentConversationId) {
        await createNewConversation();
    }

    // 设置为生成状态（禁用输入，显示暂停按钮）
    setInputState(true);
    elements.messageInput.value = '';

    // 显示用户消息
    appendMessage('user', message);

    // 显示加载动画
    appendLoadingIndicator();

    // 直接从下拉框获取当前选择的模型
    const modelName = elements.modelSelect.value;
    console.log('发送消息使用的模型:', modelName);

    // 创建 AbortController 用于中断请求
    abortController = new AbortController();

    try {
        console.log('[Chat] 发送请求, conversation_id:', currentConversationId);
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            },
            body: JSON.stringify({
                conversation_id: currentConversationId,
                message: message,
                model_name: modelName
            }),
            signal: abortController.signal
        });

        console.log('[Chat] 响应状态:', response.status, 'ok:', response.ok);
        console.log('[Chat] response.body:', response.body);

        // 注意：不要在这里移除加载动画，要等流式处理完成后再移除

        if (!response.ok) {
            console.error('[Chat] 响应错误:', response.status);
            const errorData = await response.text();
            console.error('[Chat] 错误响应:', errorData);
            removeLoadingIndicator();  // 只有错误时才立即移除
            appendMessage('assistant', '抱歉，发生错误: ' + response.status);
            setInputState(false);
            return;
        }

        try {
            // 流式响应处理
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = '';
            let isFirstChunk = true;  // 标记是否第一个数据块
            
            console.log('[SSE] 开始读取流');

            // 创建 AI 消息容器（初始为空，等待内容）
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message assistant';
            messageDiv.innerHTML = `<div class="message-avatar">🤖</div><div class="message-content"></div>`;
            const responseContent = messageDiv.querySelector('.message-content');

            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;

                const text = decoder.decode(value, { stream: true });
                
                // 简单处理：按行分割
                const lines = text.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6).trim();
                        if (data === '[DONE]') continue;
                        if (!data) continue;
                        
                        try {
                            const parsed = JSON.parse(data);
                            if (parsed.content) {
                                // 如果是第一个内容块，替换思考提示为AI消息
                                if (isFirstChunk) {
                                    removeLoadingIndicator();
                                    elements.messagesContainer.appendChild(messageDiv);
                                    isFirstChunk = false;
                                }
                                
                                assistantMessage += parsed.content;
                                // 使用Markdown渲染
                                responseContent.innerHTML = renderMessageContent(assistantMessage);
                                scrollToBottom();
                            }
                        } catch (e) {
                            console.warn('[SSE] 解析失败:', data);
                        }
                    }
                }
            }

            // 如果没有收到任何内容（AI快速响应的情况）
            if (isFirstChunk && assistantMessage === '') {
                removeLoadingIndicator();
            }

            console.log('[SSE] 完成, 内容:', assistantMessage);

            // 恢复正常状态
            setInputState(false);

            // 更新会话列表
            const conv = conversations.find(c => c.id === currentConversationId);
            if (conv && conv.title === '新对话') {
                conv.title = message.slice(0, 20) + (message.length > 20 ? '...' : '');
                renderConversationList();
            }

            await loadConversations();
        } catch (sseError) {
            // 检查是否是用户主动中断
            if (sseError.name === 'AbortError') {
                console.log('[Chat] 请求已被用户中断');
                return;
            }
            console.error('[SSE] 流式读取错误:', sseError);
            appendMessage('assistant', '抱歉，发生错误: ' + sseError.message);
            setInputState(false);
        }
    } catch (e) {
        removeLoadingIndicator();
        // 检查是否是用户主动中断
        if (e.name === 'AbortError') {
            console.log('[Chat] 请求已被用户中断');
            return;
        }
        console.error('发送消息失败:', e);
        appendMessage('assistant', '抱歉，网络错误，请重试');
        setInputState(false);
    }
}

// 处理中断
async function handleAbort() {
    console.log('[Chat] 处理中断，删除对话内容');
    
    // 移除加载动画
    removeLoadingIndicator();
    
    // 移除AI未完成的回复
    const messages = elements.messagesContainer.querySelectorAll('.message.assistant');
    if (messages.length > 0) {
        const lastAssistantMsg = messages[messages.length - 1];
        // 检查是否还有用户消息在后面
        const userMessages = elements.messagesContainer.querySelectorAll('.message.user');
        if (userMessages.length > 0) {
            const lastUserMsg = userMessages[userMessages.length - 1];
            // 如果AI消息在最后一个用户消息之后，删除它
            if (lastAssistantMsg.compareDocumentPosition(lastUserMsg) & Node.DOCUMENT_POSITION_FOLLOWING) {
                lastAssistantMsg.remove();
            }
        }
    }
    
    // 恢复正常状态
    setInputState(false);
    
    // 调用后端删除会话（可选：如果后端支持的话）
    // 这里我们保留会话，只删除AI未完成的回复
    // 如果需要完全删除会话，可以调用 deleteConversation(currentConversationId)
    
    console.log('[Chat] 中断处理完成');
}

// ============ Skills 管理 ============
let skillsData = [];

async function loadSkills() {
    try {
        const response = await fetch('/api/skills', {
            headers: getAuthHeader()
        });
        if (response.ok) {
            const data = await response.json();
            skillsData = data.skills;
            const countEl = document.getElementById('skills-count');
            if (countEl) {
                countEl.textContent = `Skills: ${data.total} | ${data.enabled}`;
            }
        }
    } catch (e) {
        console.error('加载Skills失败:', e);
    }
}

async function loadSkillsList() {
    try {
        const response = await fetch('/api/skills', {
            headers: getAuthHeader()
        });
        if (response.ok) {
            const data = await response.json();
            skillsData = data.skills;
            
            // 更新统计
            const totalEl = document.getElementById('skills-total');
            const enabledEl = document.getElementById('skills-enabled');
            if (totalEl) totalEl.textContent = data.total;
            if (enabledEl) enabledEl.textContent = data.enabled;
            
            // 渲染列表
            renderSkillsList();
        }
    } catch (e) {
        console.error('加载Skills列表失败:', e);
    }
}

function renderSkillsList() {
    const listEl = document.getElementById('skills-list');
    if (!listEl) return;
    
    listEl.innerHTML = '';
    
    if (skillsData.length === 0) {
        listEl.innerHTML = `
            <div class="skills-empty">
                <p>暂无已导入的 Skills</p>
                <p style="font-size: 12px;">点击「导入 Skill」选择本地的 SKILL.md 文件</p>
            </div>
        `;
        return;
    }
    
    skillsData.forEach(skill => {
        const item = document.createElement('div');
        item.className = 'skill-item';
        item.innerHTML = `
            <div class="skill-toggle ${skill.is_enabled ? 'active' : ''}" data-id="${skill.id}"></div>
            <div class="skill-info">
                <div class="skill-name">${skill.name}</div>
                <div class="skill-description">${skill.description || '无描述'}</div>
            </div>
            <button class="skill-delete" data-id="${skill.id}">删除</button>
        `;
        
        // 绑定切换事件
        const toggle = item.querySelector('.skill-toggle');
        toggle.addEventListener('click', () => toggleSkill(skill.id));
        
        // 绑定删除事件
        const deleteBtn = item.querySelector('.skill-delete');
        deleteBtn.addEventListener('click', () => deleteSkill(skill.id));
        
        listEl.appendChild(item);
    });
}

async function toggleSkill(skillId) {
    try {
        const response = await fetch(`/api/skills/${skillId}/toggle`, {
            method: 'POST',
            headers: getAuthHeader()
        });
        if (response.ok) {
            const data = await response.json();
            await loadSkills();
            await loadSkillsList();
        }
    } catch (e) {
        console.error('切换Skill状态失败:', e);
        alert('切换失败，请重试');
    }
}

async function deleteSkill(skillId) {
    if (!confirm('确定要删除这个 Skill 吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/skills/${skillId}`, {
            method: 'DELETE',
            headers: getAuthHeader()
        });
        if (response.ok) {
            await loadSkills();
            await loadSkillsList();
        }
    } catch (e) {
        console.error('删除Skill失败:', e);
        alert('删除失败，请重试');
    }
}

async function handleSkillFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    // 显示导入提示
    const importBtn = document.getElementById('import-skill-btn');
    const originalText = importBtn ? importBtn.textContent : '导入';
    if (importBtn) {
        importBtn.textContent = '导入中...';
        importBtn.disabled = true;
    }
    
    try {
        const response = await fetch('/api/skills', {
            method: 'POST',
            headers: getAuthHeader(),
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            alert(`✅ ${data.message}\n\n名称: ${data.name}\n描述: ${data.description}`);
            await loadSkills();
            await loadSkillsList();
        } else {
            const error = await response.json();
            alert('❌ 导入失败: ' + (error.detail || '未知错误'));
        }
    } catch (e) {
        console.error('导入Skill失败:', e);
        alert('❌ 导入失败，请重试');
    } finally {
        // 恢复按钮状态
        if (importBtn) {
            importBtn.textContent = originalText;
            importBtn.disabled = false;
        }
    }
    
    // 清空文件选择
    e.target.value = '';
}

// 处理文件夹选择上传（推荐方式）
async function handleSkillFolderSelect(e) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    // 获取第一个文件，它应该包含文件夹路径信息
    const firstFile = files[0];
    const webkitRelativePath = firstFile.webkitRelativePath;
    
    // 验证文件夹中是否有 SKILL.md
    let hasSkillMd = false;
    for (let i = 0; i < files.length; i++) {
        if (files[i].name === 'SKILL.md' || files[i].webkitRelativePath.endsWith('/SKILL.md')) {
            hasSkillMd = true;
            break;
        }
    }
    
    if (!hasSkillMd) {
        alert('❌ 导入失败: 文件夹中未找到 SKILL.md 文件');
        e.target.value = '';
        return;
    }
    
    // 显示导入提示
    const importBtn = document.getElementById('import-skill-folder-btn');
    const originalText = importBtn ? importBtn.textContent : '选择文件夹';
    if (importBtn) {
        importBtn.textContent = '导入中...';
        importBtn.disabled = true;
    }
    
    try {
        // 创建 FormData
        const formData = new FormData();
        
        // 添加文件夹中的所有文件
        // 注意：浏览器会传递整个文件夹结构
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }
        
        // 传递文件夹路径信息
        const folderPath = webkitRelativePath.split('/')[0];
        formData.append('folder_name', folderPath);
        
        const response = await fetch('/api/skills', {
            method: 'POST',
            headers: getAuthHeader(),
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            alert(`✅ ${data.message}\n\n名称: ${data.name}\n描述: ${data.description}`);
            await loadSkills();
            await loadSkillsList();
        } else {
            const error = await response.json();
            alert('❌ 导入失败: ' + (error.detail || '未知错误'));
        }
    } catch (e) {
        console.error('导入Skill(文件夹)失败:', e);
        alert('❌ 导入失败，请重试');
    } finally {
        // 恢复按钮状态
        if (importBtn) {
            importBtn.textContent = originalText;
            importBtn.disabled = false;
        }
    }
    
    // 清空文件夹选择
    e.target.value = '';
}