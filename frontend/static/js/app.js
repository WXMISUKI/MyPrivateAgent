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

// 渲染消息内容（支持推理过程分离）
function renderMessageWithReasoning(content, reasoningContent = null, loadingClass = '') {
    // 如果有独立的推理内容，使用新的渲染方式
    if (reasoningContent) {
        const reasoningId = 'reasoning-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

        let html = `
            <div class="reasoning-section expanded">
                <div class="reasoning-header" onclick="toggleReasoning(this)">
                    <span class="reasoning-icon">🧠</span>
                    <span class="reasoning-title">思考过程${loadingClass ? ' (思考中...)' : ''}</span>
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="reasoning-content ${loadingClass}">
                    ${renderMessageContent(reasoningContent)}
                </div>
            </div>
            <div class="answer-section">
                <div class="message-content assistant-message-content">
                    ${renderMessageContent(content)}
                </div>
            </div>
        `;

        return html;
    }

    // 检测是否包含推理过程（旧格式兼容）
    const reasoningStart = content.indexOf('📊 任务评估');
    const reasoningEnd = content.indexOf('=');

    if (reasoningStart !== -1 && reasoningEnd !== -1) {
        // 提取推理过程
        const reasoningText = content.substring(reasoningStart, reasoningEnd).trim();
        // 提取实际输出
        const actualContent = content.substring(reasoningEnd + 1).trim();

        // 生成唯一ID
        const reasoningId = 'reasoning-' + Date.now();

        // 构建HTML
        let html = `
            <div class="reasoning-section expanded">
                <div class="reasoning-header" onclick="toggleReasoning(this)">
                    <span class="reasoning-icon">🧠</span>
                    <span class="reasoning-title">思考过程</span>
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="reasoning-content">
                    <pre>${escapeHtml(reasoningText)}</pre>
                </div>
            </div>
            <div class="answer-section">
                <div class="message-content">
                    ${renderMessageContent(actualContent)}
                </div>
            </div>
        `;

        return html;
    }

    // 如果没有推理过程，直接渲染（添加背景色）
    return `<div class="message-content assistant-message-content">${renderMessageContent(content)}</div>`;
}

// 切换推理过程显示/隐藏
window.toggleReasoning = function(headerElement) {
    const section = headerElement.parentElement;
    section.classList.toggle('expanded');
};

// HTML转义函数
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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
    agentModeIndicator: document.getElementById('agent-mode-indicator'),
    contextStatsIndicator: document.getElementById('context-stats-indicator'),
    contextUsage: document.getElementById('context-usage'),
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
    skillFileInput: document.getElementById('skill-file-input'),
    // 权限对话框
    permissionDialog: document.getElementById('permission-dialog'),
    permissionToolName: document.getElementById('permission-tool-name'),
    permissionToolDesc: document.getElementById('permission-tool-desc'),
    permissionToolArgs: document.getElementById('permission-tool-args'),
    permissionApproveBtn: document.getElementById('permission-approve-btn'),
    permissionDenyBtn: document.getElementById('permission-deny-btn')
};

function getAuthHeader() {
    const token = localStorage.getItem('access_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// ============ 权限对话框相关 ============

let currentPermissionCallback = null;

function bindPermissionDialogEvents() {
    if (elements.permissionApproveBtn) {
        elements.permissionApproveBtn.addEventListener('click', async () => {
            await handlePermissionResponse(true);
        });
    }

    if (elements.permissionDenyBtn) {
        elements.permissionDenyBtn.addEventListener('click', async () => {
            await handlePermissionResponse(false);
        });
    }
}

function showPermissionDialog(toolName, toolDesc, toolArgs, callback) {
    if (!elements.permissionDialog) return;

    currentPermissionCallback = callback;

    if (elements.permissionToolName) {
        elements.permissionToolName.textContent = toolName;
    }

    if (elements.permissionToolDesc) {
        elements.permissionToolDesc.textContent = toolDesc || '无描述';
    }

    if (elements.permissionToolArgs) {
        elements.permissionToolArgs.textContent = JSON.stringify(toolArgs, null, 2);
    }

    elements.permissionDialog.style.display = 'block';
}

function hidePermissionDialog() {
    if (elements.permissionDialog) {
        elements.permissionDialog.style.display = 'none';
    }
    currentPermissionCallback = null;
}

async function handlePermissionResponse(approved) {
    if (!currentPermissionCallback) return;

    const callback = currentPermissionCallback;
    currentPermissionCallback = null;
    hidePermissionDialog();

    if (approved) {
        callback.resolve('approved');
    } else {
        callback.reject(new Error('权限被拒绝'));
    }
}

// 轮询检查权限请求
let permissionPollInterval = null;

function startPermissionPolling() {
    if (permissionPollInterval) return;

    permissionPollInterval = setInterval(async () => {
        await checkPendingPermissions();
    }, 2000);
}

function stopPermissionPolling() {
    if (permissionPollInterval) {
        clearInterval(permissionPollInterval);
        permissionPollInterval = null;
    }
}

async function checkPendingPermissions() {
    try {
        const response = await fetch('/api/permissions/pending', {
            headers: getAuthHeader()
        });

        if (!response.ok) return;

        const data = await response.json();
        if (data.requests && data.requests.length > 0) {
            // 显示第一个待处理的权限请求
            const request = data.requests[0];
            showPermissionDialog(
                request.tool_name,
                `权限级别: ${request.permission_level}`,
                request.tool_args,
                {
                    resolve: async (result) => {
                        await fetch('/api/permissions/approve', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                ...getAuthHeader()
                            },
                            body: JSON.stringify({ request_id: request.id, result })
                        });
                    },
                    reject: async (error) => {
                        await fetch('/api/permissions/deny', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                ...getAuthHeader()
                            },
                            body: JSON.stringify({ request_id: request.id })
                        });
                    }
                }
            );
        }
    } catch (e) {
        console.error('[Permission] 检查待处理权限失败:', e);
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    await checkAuth();
    await loadUserInfo();
    await loadConversations();
    await loadSkills();  // 加载Skills

    // 绑定事件
    bindEvents();

    // 绑定权限对话框事件
    bindPermissionDialogEvents();
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

function appendMessage(role, content, reasoningContent = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    // AI消息使用Markdown渲染，用户消息直接显示
    // 如果有独立的推理内容，使用新的渲染方式
    if (role === 'assistant' && reasoningContent) {
        const htmlContent = renderMessageWithReasoning(content, reasoningContent);
        messageDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-body">${htmlContent}</div>
        `;
    } else {
        const htmlContent = role === 'assistant' ? renderMessageContent(content) : content.replace(/\n/g, '<br>');
        messageDiv.innerHTML = `
            <div class="message-avatar">${role === 'user' ? '👤' : '🤖'}</div>
            <div class="message-content">${htmlContent}</div>
        `;
    }
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

function createSSEChunkParser(onEvent) {
    let eventBuffer = '';
    let jsonBuffer = '';

    return {
        push(chunkText) {
            eventBuffer += chunkText || '';

            const segments = eventBuffer.split('\n\n');
            eventBuffer = segments.pop() || '';

            for (const segment of segments) {
                const lines = segment.split('\n');
                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;

                    jsonBuffer += line.slice(6);
                    try {
                        const parsed = JSON.parse(jsonBuffer);
                        jsonBuffer = '';
                        onEvent(parsed);
                    } catch (e) {
                        // 等待后续 chunk 补全 JSON
                    }
                }
            }
        },

        flush() {
            if (eventBuffer.trim()) {
                this.push('\n\n');
            }

            if (!jsonBuffer.trim()) return;

            try {
                const parsed = JSON.parse(jsonBuffer);
                jsonBuffer = '';
                onEvent(parsed);
            } catch (e) {
                console.warn('[SSE] 丢弃未完成的 JSON 片段:', jsonBuffer);
                jsonBuffer = '';
            }
        }
    };
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

    const message = elements.messageInput?.value?.trim();
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
    const modelName = elements.modelSelect?.value || 'doubao';

    // 自动判断是否显示推理（仅对支持推理的模型显示）
    const modelsWithReasoning = ['deepseek-r1:7b', 'deepseek-r1'];
    const showReasoning = modelsWithReasoning.includes(modelName);
    console.log('发送消息使用的模型:', modelName, '自动推理显示:', showReasoning);

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
                model_name: modelName,
                show_reasoning: showReasoning
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
            let reasoningMessage = '';  // 收集推理内容
            let reasoningDone = false;  // 标记推理是否完成
            let latestDoneContent = '';
            const sseParser = createSSEChunkParser(handleSSEEvent);

            console.log('[SSE] 开始读取流');

            // 创建 AI 消息容器
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message assistant';

            // 先移除加载动画，添加空的消息容器
            removeLoadingIndicator();
            elements.messagesContainer.appendChild(messageDiv);

            // 用于更新内容（带去重和动画）
            let lastContent = '';
            let lastReasoning = '';
            let isStreaming = true;
            const updateMessageContent = (content, reasoning = null, showLoading = false) => {
                // 去重：如果内容和上次一样，不重复渲染
                if (content === lastContent && reasoning === lastReasoning) {
                    return;
                }
                lastContent = content;
                lastReasoning = reasoning || '';

                const loadingClass = showLoading && reasoning ? ' reasoning-loading' : '';
                const streamingClass = isStreaming ? ' streaming' : '';
                messageDiv.innerHTML = `
                    <div class="message-avatar">🤖</div>
                    <div class="message-body${streamingClass}">
                        ${renderMessageWithReasoning(content, reasoning, loadingClass)}
                    </div>
                `;
                scrollToBottom();
            };

            // 标记流式结束
            const finishStreaming = () => {
                isStreaming = false;
                const body = messageDiv.querySelector('.message-body');
                if (body) {
                    body.classList.remove('streaming');
                }
            };

            // 初始空内容
            updateMessageContent('', '');

            function handleSSEEvent(parsed) {
                const type = parsed.type;
                console.log('[SSE] 收到数据:', type, parsed);

                if (type === 'conversation_id' && parsed.conversation_id) {
                    currentConversationId = parsed.conversation_id;
                    return;
                }

                if (type === 'reasoning') {
                    reasoningMessage += parsed.content || '';
                    updateMessageContent(assistantMessage, reasoningMessage, true);
                    return;
                }

                if (type === 'status') {
                    console.log('[SSE] 状态:', parsed.content);
                    return;
                }

                if (type === 'answer' || type === 'content') {
                    assistantMessage += parsed.content || '';
                    updateMessageContent(assistantMessage, reasoningMessage);
                    return;
                }

                if (type === 'done') {
                    reasoningDone = true;
                    latestDoneContent = parsed.content || latestDoneContent || '';
                    if (latestDoneContent) {
                        assistantMessage = latestDoneContent;
                    }
                    const finalReasoning = parsed.reasoning_content || reasoningMessage;
                    updateMessageContent(assistantMessage, finalReasoning, false);
                    finishStreaming();

                    if (parsed.context_stats && elements.contextStatsIndicator) {
                        const stats = parsed.context_stats;
                        const tokens = stats.tokens || 0;
                        const messages = stats.messages || 0;
                        const compression = stats.compression_count || 0;

                        elements.contextStatsIndicator.style.display = 'flex';
                        elements.contextUsage.textContent = `Tokens: ${tokens} | Messages: ${messages}${compression > 0 ? ` | Compressed: ${compression}x` : ''}`;

                        elements.contextStatsIndicator.className = 'context-stats-indicator';
                        if (tokens > 6000) {
                            elements.contextStatsIndicator.classList.add('danger');
                        } else if (tokens > 4000) {
                            elements.contextStatsIndicator.classList.add('warning');
                        }
                    }

                    console.log('[SSE] 完成');
                    return;
                }

                if (type === 'error') {
                    finishStreaming();
                    assistantMessage += '\n\n' + (parsed.content || parsed.error || '发生错误');
                    updateMessageContent(assistantMessage, '');
                    return;
                }

                if (parsed.content && !type) {
                    assistantMessage += parsed.content;
                    updateMessageContent(assistantMessage, reasoningMessage);
                }
            }

            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                const text = decoder.decode(value, { stream: true });
                sseParser.push(text);
            }

            sseParser.flush();

            console.log('[SSE] 完成, 内容长度:', assistantMessage.length, '推理内容长度:', reasoningMessage.length);

            // 隐藏多智能体模式指示器
            setTimeout(() => {
                elements.agentModeIndicator.style.display = 'none';
            }, 3000);

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

// ============ 学习记录管理 ============

// 学习记录管理相关元素
const learningsElements = {
    learningsButton: document.getElementById('learnings-button'),
    learningsModal: document.getElementById('learnings-modal'),
    learningsClose: document.getElementById('learnings-close'),
    learningsStats: document.getElementById('learnings-stats'),
    learningsTotal: document.getElementById('learnings-total'),
    learningsPending: document.getElementById('learnings-pending'),
    learningsResolved: document.getElementById('learnings-resolved'),
    learningsErrors: document.getElementById('learnings-errors'),
    learningsFeatures: document.getElementById('learnings-features'),
    runDailyReviewBtn: document.getElementById('run-daily-review-btn'),
    runAutoPromoteBtn: document.getElementById('run-auto-promote-btn'),
    createLearningBtn: document.getElementById('create-learning-btn'),
    learningsList: document.getElementById('learnings-list'),
    errorsList: document.getElementById('errors-list'),
    featuresList: document.getElementById('features-list'),
    trendsContent: document.getElementById('trends-content'),
    createLearningModal: document.getElementById('create-learning-modal'),
    createLearningClose: document.getElementById('create-learning-close'),
    createLearningForm: document.getElementById('create-learning-form'),
    cancelCreateLearning: document.getElementById('cancel-create-learning'),
    refreshTrendsBtn: document.getElementById('refresh-trends-btn'),
    trendsDays: document.getElementById('trends-days')
};

// 打开学习记录管理面板
if (learningsElements.learningsButton && learningsElements.learningsModal) {
    learningsElements.learningsButton.addEventListener('click', () => {
        learningsElements.learningsModal.style.display = 'flex';
        loadLearningsStats();
        loadLearningsList();
    });
}

// 关闭学习记录管理面板
if (learningsElements.learningsClose) {
    learningsElements.learningsClose.addEventListener('click', () => {
        learningsElements.learningsModal.style.display = 'none';
    });
}

// 加载学习记录统计
async function loadLearningsStats() {
    try {
        const response = await fetch('/api/learnings/stats', {
            headers: getAuthHeader()
        });
        
        if (response.ok) {
            const stats = await response.json();
            learningsElements.learningsTotal.textContent = stats.total_learnings;
            learningsElements.learningsPending.textContent = stats.pending_learnings;
            learningsElements.learningsResolved.textContent = stats.resolved_learnings;
            learningsElements.learningsErrors.textContent = stats.total_errors;
            learningsElements.learningsFeatures.textContent = stats.total_features;
        }
    } catch (e) {
        console.error('加载学习记录统计失败:', e);
    }
}

// 加载学习记录列表
async function loadLearningsList(statusFilter = '', categoryFilter = '') {
    try {
        let url = '/api/learnings/learnings?limit=50';
        if (statusFilter) url += `&status=${statusFilter}`;
        if (categoryFilter) url += `&category=${categoryFilter}`;
        
        const response = await fetch(url, {
            headers: getAuthHeader()
        });
        
        if (response.ok) {
            const learnings = await response.json();
            renderLearningsList(learnings);
        }
    } catch (e) {
        console.error('加载学习记录列表失败:', e);
    }
}

// 渲染学习记录列表
function renderLearningsList(learnings) {
    if (!learnings || learnings.length === 0) {
        learningsElements.learningsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📚</div>
                <div class="empty-state-text">暂无学习记录</div>
            </div>
        `;
        return;
    }
    
    learningsElements.learningsList.innerHTML = learnings.map(learning => `
        <div class="learning-item">
            <div class="learning-header">
                <span class="learning-id">${learning.learning_id}</span>
                <span class="learning-status status-${learning.status}">${getStatusText(learning.status)}</span>
            </div>
            <div class="learning-summary">${escapeHtml(learning.summary)}</div>
            ${learning.details ? `<div class="learning-details">${escapeHtml(learning.details)}</div>` : ''}
            <div class="learning-actions">
                <span class="priority-${learning.priority}">${getPriorityText(learning.priority)}</span>
                <span class="category-${learning.category}">${getCategoryText(learning.category)}</span>
                ${learning.status === 'pending' ? `
                    <button class="action-btn primary" onclick="resolveLearning('${learning.learning_id}')">解决</button>
                ` : ''}
            </div>
        </div>
    `).join('');
}

// 加载错误记录列表
async function loadErrorsList(statusFilter = '') {
    try {
        let url = '/api/learnings/errors?limit=50';
        if (statusFilter) url += `&status=${statusFilter}`;
        
        const response = await fetch(url, {
            headers: getAuthHeader()
        });
        
        if (response.ok) {
            const errors = await response.json();
            renderErrorsList(errors);
        }
    } catch (e) {
        console.error('加载错误记录列表失败:', e);
    }
}

// 渲染错误记录列表
function renderErrorsList(errors) {
    if (!errors || errors.length === 0) {
        learningsElements.errorsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🐛</div>
                <div class="empty-state-text">暂无错误记录</div>
            </div>
        `;
        return;
    }
    
    learningsElements.errorsList.innerHTML = errors.map(error => `
        <div class="error-item">
            <div class="error-header">
                <span class="error-id">${error.error_id}</span>
                <span class="error-status status-${error.status}">${getStatusText(error.status)}</span>
            </div>
            <div class="error-summary">${escapeHtml(error.summary)}</div>
            ${error.error_message ? `<div class="error-context">${escapeHtml(error.error_message)}</div>` : ''}
            ${error.suggested_fix ? `<div class="error-context"><strong>建议修复:</strong> ${escapeHtml(error.suggested_fix)}</div>` : ''}
        </div>
    `).join('');
}

// 加载功能请求列表
async function loadFeaturesList(statusFilter = '') {
    try {
        let url = '/api/learnings/features?limit=50';
        if (statusFilter) url += `&status=${statusFilter}`;
        
        const response = await fetch(url, {
            headers: getAuthHeader()
        });
        
        if (response.ok) {
            const features = await response.json();
            renderFeaturesList(features);
        }
    } catch (e) {
        console.error('加载功能请求列表失败:', e);
    }
}

// 渲染功能请求列表
function renderFeaturesList(features) {
    if (!features || features.length === 0) {
        learningsElements.featuresList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">💡</div>
                <div class="empty-state-text">暂无功能请求</div>
            </div>
        `;
        return;
    }
    
    learningsElements.featuresList.innerHTML = features.map(feature => `
        <div class="feature-item">
            <div class="feature-header">
                <span class="feature-id">${feature.feature_id}</span>
                <span class="feature-status status-${feature.status}">${getStatusText(feature.status)}</span>
            </div>
            <div class="feature-request">${escapeHtml(feature.requested_capability)}</div>
            ${feature.user_context ? `<div class="feature-context">${escapeHtml(feature.user_context)}</div>` : ''}
        </div>
    `).join('');
}

// 运行每日复盘
if (learningsElements.runDailyReviewBtn) {
    learningsElements.runDailyReviewBtn.addEventListener('click', async () => {
        try {
            const originalText = learningsElements.runDailyReviewBtn.textContent;
            learningsElements.runDailyReviewBtn.textContent = '分析中...';
            learningsElements.runDailyReviewBtn.disabled = true;
            
            const response = await fetch('/api/learnings/review/daily', {
                method: 'POST',
                headers: getAuthHeader()
            });
            
            if (response.ok) {
                const result = await response.json();
                
                if (result.success) {
                    let reviewText = `✅ 每日复盘完成\n\n`;
                    
                    if (result.summary.summary) {
                        reviewText += `📊 复盘总结:\n${result.summary.summary}\n\n`;
                    }
                    
                    if (result.optimization_suggestions.suggestions.length > 0) {
                        reviewText += `💡 优化建议:\n${result.optimization_suggestions.suggestions.join('\n\n')}\n\n`;
                    }
                    
                    if (result.priority_suggestions.priorities.length > 0) {
                        reviewText += `🎯 优先级建议:\n`;
                        result.priority_suggestions.priorities.forEach(p => {
                            reviewText += `- ${p.type}: ${p.count}个 - ${p.suggestion}\n`;
                        });
                    }
                    
                    alert(reviewText);
                    loadLearningsStats();
                    loadLearningsList();
                } else {
                    alert('❌ 复盘失败: ' + (result.error || '未知错误'));
                }
            } else {
                alert('❌ 复盘失败: ' + (await response.text()));
            }
        } catch (e) {
            console.error('运行每日复盘失败:', e);
            alert('❌ 复盘失败，请重试');
        } finally {
            learningsElements.runDailyReviewBtn.textContent = '📊 运行每日复盘';
            learningsElements.runDailyReviewBtn.disabled = false;
        }
    });
}

// 运行自动提升
if (learningsElements.runAutoPromoteBtn) {
    learningsElements.runAutoPromoteBtn.addEventListener('click', async () => {
        try {
            const originalText = learningsElements.runAutoPromoteBtn.textContent;
            learningsElements.runAutoPromoteBtn.textContent = '提升中...';
            learningsElements.runAutoPromoteBtn.disabled = true;
            
            const response = await fetch('/api/learnings/review/promote?min_recurrence=3', {
                method: 'POST',
                headers: getAuthHeader()
            });
            
            if (response.ok) {
                const result = await response.json();
                
                if (result.total > 0) {
                    let promoteText = `✅ 自动提升完成\n\n`;
                    promoteText += `总计: ${result.total}个\n`;
                    promoteText += `成功: ${result.successful}个\n`;
                    promoteText += `失败: ${result.failed}个\n`;
                    
                    alert(promoteText);
                    loadLearningsStats();
                    loadLearningsList();
                } else {
                    alert('✅ 没有需要提升的学习记录');
                }
            } else {
                alert('❌ 提升失败: ' + (await response.text()));
            }
        } catch (e) {
            console.error('运行自动提升失败:', e);
            alert('❌ 提升失败，请重试');
        } finally {
            learningsElements.runAutoPromoteBtn.textContent = '🚀 自动提升学习记录';
            learningsElements.runAutoPromoteBtn.disabled = false;
        }
    });
}

// 打开创建学习记录表单
if (learningsElements.createLearningBtn) {
    learningsElements.createLearningBtn.addEventListener('click', () => {
        learningsElements.createLearningModal.style.display = 'flex';
    });
}

// 关闭创建学习记录表单
if (learningsElements.createLearningClose) {
    learningsElements.createLearningClose.addEventListener('click', () => {
        learningsElements.createLearningModal.style.display = 'none';
        learningsElements.createLearningForm.reset();
    });
}

if (learningsElements.cancelCreateLearning) {
    learningsElements.cancelCreateLearning.addEventListener('click', () => {
        learningsElements.createLearningModal.style.display = 'none';
        learningsElements.createLearningForm.reset();
    });
}

// 提交创建学习记录表单
if (learningsElements.createLearningForm) {
    learningsElements.createLearningForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            category: document.getElementById('learning-category').value,
            priority: document.getElementById('learning-priority').value,
            summary: document.getElementById('learning-summary').value,
            details: document.getElementById('learning-details').value,
            suggested_action: document.getElementById('learning-action').value,
            source: 'manual'
        };
        
        try {
            const response = await fetch('/api/learnings/learnings', {
                method: 'POST',
                headers: {
                    ...getAuthHeader(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                alert('✅ 学习记录创建成功');
                learningsElements.createLearningModal.style.display = 'none';
                learningsElements.createLearningForm.reset();
                loadLearningsStats();
                loadLearningsList();
            } else {
                const error = await response.json();
                alert('❌ 创建失败: ' + (error.detail || '未知错误'));
            }
        } catch (e) {
            console.error('创建学习记录失败:', e);
            alert('❌ 创建失败，请重试');
        }
    });
}

// 选项卡切换
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // 移除所有选项卡的激活状态
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        
        // 激活当前选项卡
        btn.classList.add('active');
        const tabName = btn.dataset.tab;
        document.getElementById(`tab-${tabName}`).classList.add('active');
        
        // 加载对应的数据
        if (tabName === 'learnings') {
            loadLearningsList();
        } else if (tabName === 'errors') {
            loadErrorsList();
        } else if (tabName === 'features') {
            loadFeaturesList();
        } else if (tabName === 'trends') {
            loadTrends();
        }
    });
});

// 加载趋势分析
async function loadTrends() {
    try {
        const days = learningsElements.trendsDays.value || 7;
        const response = await fetch(`/api/learnings/review/trends?days=${days}`, {
            headers: getAuthHeader()
        });
        
        if (response.ok) {
            const trends = await response.json();
            renderTrends(trends);
        }
    } catch (e) {
        console.error('加载趋势分析失败:', e);
    }
}

// 渲染趋势分析
function renderTrends(trends) {
    if (!trends || !trends.trends || Object.keys(trends.trends).length === 0) {
        learningsElements.trendsContent.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📈</div>
                <div class="empty-state-text">暂无趋势数据</div>
            </div>
        `;
        return;
    }
    
    let html = `<h4>📊 学习趋势 (最近${trends.days}天)</h4>`;
    
    // 按日期排序
    const sortedDates = Object.keys(trends.trends).sort();
    
    sortedDates.forEach(date => {
        const dateData = trends.trends[date];
        const total = Object.values(dateData).reduce((sum, count) => sum + count, 0);
        
        html += `
            <div style="margin: 12px 0; padding: 12px; background: white; border-radius: 6px; border: 1px solid #e2e8f0;">
                <div style="font-weight: 600; margin-bottom: 8px; color: #334155;">${date} (总计: ${total})</div>
        `;
        
        Object.entries(dateData).forEach(([category, count]) => {
            html += `
                <div style="display: flex; justify-content: space-between; margin: 4px 0; font-size: 13px;">
                    <span style="color: #64748b;">${getCategoryText(category)}</span>
                    <span style="color: #334155; font-weight: 500;">${count}</span>
                </div>
            `;
        });
        
        html += `</div>`;
    });
    
    learningsElements.trendsContent.innerHTML = html;
}

// 刷新趋势分析
if (learningsElements.refreshTrendsBtn) {
    learningsElements.refreshTrendsBtn.addEventListener('click', loadTrends);
}

// 解决学习记录
window.resolveLearning = async function(learningId) {
    try {
        const response = await fetch(`/api/learnings/learnings/${learningId}/resolve`, {
            method: 'PUT',
            headers: getAuthHeader()
        });
        
        if (response.ok) {
            alert('✅ 学习记录已解决');
            loadLearningsStats();
            loadLearningsList();
        } else {
            alert('❌ 解决失败: ' + (await response.text()));
        }
    } catch (e) {
        console.error('解决学习记录失败:', e);
        alert('❌ 解决失败，请重试');
    }
};

// 辅助函数
function getStatusText(status) {
    const statusMap = {
        'pending': '待处理',
        'resolved': '已解决',
        'promoted': '已提升'
    };
    return statusMap[status] || status;
}

function getPriorityText(priority) {
    const priorityMap = {
        'critical': '关键',
        'high': '高',
        'medium': '中',
        'low': '低'
    };
    return priorityMap[priority] || priority;
}

function getCategoryText(category) {
    const categoryMap = {
        'correction': '纠正',
        'insight': '洞察',
        'knowledge_gap': '知识差距',
        'best_practice': '最佳实践'
    };
    return categoryMap[category] || category;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
