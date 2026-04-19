# MyPrivateAgent 思考过程展示方案

## 文档信息
- **创建日期**: 2026-04-17
- **版本**: v1.0
- **状态**: 待评审
- **优先级**: 🔴 高

---

## 一、需求概述

### 1.1 用户需求

在对话框中展示大模型的思考过程，支持点击展开/收缩，思考过程默认展开显示。

### 1.2 当前问题

- 推理内容与最终答案混排显示
- 不支持折叠/展开交互
- 用户无法方便地查看/隐藏思考过程
- 整体视觉体验较差

### 1.3 目标

- 思考过程与最终答案分离展示
- 支持点击展开/收缩功能
- 默认展开显示思考过程
- 支持 Markdown 渲染
- 视觉上清晰区分思考过程和最终答案

---

## 二、竞品分析

### 2.1 主流智能体展示方式

| 智能体 | 展示方式 | 特点 |
|--------|----------|------|
| Claude Code | 折叠面板 | 点击 "Thinking" 展开详情，带动画效果 |
| ChatGPT | 流式显示 | 思考过程逐步显示，无单独折叠 |
| DeepSeek | 独立区块 | 推理过程单独展示，带标签 |
| 通义千问 | 折叠面板 | 点击"深度思考"展开，带旋转图标 |

### 2.2 推荐方案

采用 **折叠面板 + 独立区块** 方案：
- 思考过程作为独立区块展示
- 带展开/收缩按钮
- 默认展开，支持点击收缩
- 清晰的视觉区分

---

## 三、技术方案

### 3.1 后端修改

#### 3.1.1 SSE 响应格式修改

当前格式：
```json
data: {"content": "最终答案", "model": "deepseek-r1:7b"}
```

修改后格式：
```json
data: {"content": "最终答案", "reasoning_content": "推理过程", "model": "deepseek-r1:7b", "reasoning_done": true}
```

**字段说明**：
- `content`: 最终答案内容
- `reasoning_content`: 思考过程内容
- `model`: 使用的模型
- `reasoning_done`: 推理是否完成（用于前端控制展开/收起）

#### 3.1.2 代码修改

**文件**: `backend/orchestrator.py`

```python
async def _process_single_agent(
    self,
    user_message: str,
    model_name: str
) -> AsyncGenerator[str, None]:
    """单智能体模式处理"""

    try:
        # 获取模型和适配器
        model = self.model_router.get_model(model_name)
        adapter = get_adapter(model_name)

        # 构建消息
        messages = [HumanMessage(content=user_message)]

        # 检查是否支持推理链
        model_config = self.model_router.get_model_config(model_name)
        supports_reasoning = model_config.get("supports_reasoning", False)

        # 流式输出
        full_response = ""
        reasoning_content = ""

        async for chunk in model.astream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                content = chunk.content
                full_response += content
                yield content

            # 收集推理内容（如果是推理模型）
            if supports_reasoning:
                # 尝试从 chunk 中提取 reasoning_content
                reasoning = self._extract_reasoning(chunk)
                if reasoning:
                    reasoning_content += reasoning
                    # 实时推送推理内容
                    yield json.dumps({
                        "type": "reasoning",
                        "content": reasoning
                    }) + "\n"

        # 推理完成后，发送完成信号
        yield json.dumps({
            "type": "done",
            "content": full_response,
            "reasoning_content": reasoning_content if reasoning_content else None
        }) + "\n"

    except Exception as e:
        yield f"❌ 错误: {str(e)}"

def _extract_reasoning(self, chunk) -> str:
    """从 chunk 中提取推理内容"""
    # 根据不同模型提取 reasoning_content
    if hasattr(chunk, 'response_metadata'):
        return chunk.response_metadata.get('reasoning_content', '')

    # DeepSeek 特定处理
    if hasattr(chunk, 'raw') and chunk.raw:
        delta = chunk.raw.get('choices', [{}])[0].get('delta', {})
        return delta.get('reasoning_content', '')

    return ''
```

### 3.2 前端修改

#### 3.2.1 消息展示结构

```html
<!-- AI 回复消息结构 -->
<div class="message assistant-message" data-message-id="xxx">
    <!-- 思考过程区域（默认展开）-->
    <div class="reasoning-section expanded">
        <div class="reasoning-header" onclick="toggleReasoning(this)">
            <span class="reasoning-icon">🧠</span>
            <span class="reasoning-title">思考过程</span>
            <span class="toggle-icon">▼</span>
        </div>
        <div class="reasoning-content">
            <!-- Markdown 渲染的思考内容 -->
        </div>
    </div>

    <!-- 最终答案区域 -->
    <div class="answer-section">
        <div class="message-content">
            <!-- Markdown 渲染的最终答案 -->
        </div>
    </div>
</div>
```

#### 3.2.2 CSS 样式

```css
/* 思考过程区域 */
.reasoning-section {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin-bottom: 12px;
    background: #f8f9fa;
    overflow: hidden;
}

.reasoning-section.expanded .reasoning-content {
    display: block;
}

.reasoning-section:not(.expanded) .reasoning-content {
    display: none;
}

/* 思考过程头部 */
.reasoning-header {
    display: flex;
    align-items: center;
    padding: 10px 14px;
    cursor: pointer;
    background: #e9ecef;
    border-bottom: 1px solid #dee2e6;
    transition: background 0.2s;
}

.reasoning-header:hover {
    background: #dee2e6;
}

.reasoning-icon {
    margin-right: 8px;
    font-size: 16px;
}

.reasoning-title {
    flex: 1;
    font-weight: 600;
    color: #495057;
    font-size: 14px;
}

.toggle-icon {
    font-size: 12px;
    color: #6c757d;
    transition: transform 0.3s;
}

.reasoning-section.expanded .toggle-icon {
    transform: rotate(180deg);
}

/* 思考过程内容 */
.reasoning-content {
    padding: 14px;
    font-size: 13px;
    line-height: 1.6;
    color: #495057;
    max-height: 300px;
    overflow-y: auto;
}

/* 最终答案区域 */
.answer-section {
    padding: 4px 0;
}

.answer-section .message-content {
    line-height: 1.7;
}
```

#### 3.2.3 JavaScript 逻辑

```javascript
// 切换思考过程展开/收缩
function toggleReasoning(headerElement) {
    const section = headerElement.parentElement;
    section.classList.toggle('expanded');
}

// 处理 SSE 流式响应
async function handleSSEStream(reader, messageDiv) {
    const decoder = new TextDecoder();
    let buffer = '';
    let reasoningContent = '';
    let answerContent = '';
    let reasoningDone = false;

    const reasoningDiv = messageDiv.querySelector('.reasoning-content');
    const answerDiv = messageDiv.querySelector('.message-content');

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // 处理多条 SSE 数据
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
            if (!line.startsWith('data: ')) continue;

            const data = line.slice(6).trim();
            if (data === '[DONE]') continue;

            try {
                const parsed = JSON.parse(data);

                // 处理推理内容
                if (parsed.type === 'reasoning' || parsed.reasoning_content) {
                    reasoningContent += parsed.reasoning_content || parsed.content || '';
                    if (reasoningDiv) {
                        reasoningDiv.innerHTML = marked.parse(reasoningContent);
                    }
                }

                // 处理完成信号
                if (parsed.type === 'done') {
                    reasoningDone = true;
                    answerContent = parsed.content;

                    // 隐藏推理加载状态
                    const reasoningSection = messageDiv.querySelector('.reasoning-section');
                    if (reasoningSection) {
                        reasoningSection.classList.add('loaded');
                    }

                    if (answerDiv) {
                        answerDiv.innerHTML = marked.parse(answerContent);
                    }
                }

                // 处理纯内容（兼容旧格式）
                if (parsed.content && !parsed.reasoning_content && parsed.type !== 'reasoning') {
                    answerContent += parsed.content;
                    if (answerDiv) {
                        answerDiv.innerHTML = marked.parse(answerContent);
                    }
                }
            } catch (e) {
                // 非 JSON 格式，直接作为内容
                if (data && data !== '[DONE]') {
                    answerContent += data;
                    if (answerDiv) {
                        answerDiv.innerHTML = marked.parse(answerContent);
                    }
                }
            }
        }
    }

    scrollToBottom();
}
```

---

## 四、实施计划

### 4.1 任务拆分

| 任务 ID | 任务名称 | 预计时间 | 依赖 |
|---------|----------|----------|------|
| 4.1.1 | 修改后端 SSE 响应格式 | 2 小时 | 无 |
| 4.1.2 | 前端消息结构改造 | 2 小时 | 4.1.1 |
| 4.1.3 | 添加折叠/展开交互 | 1 小时 | 4.1.2 |
| 4.1.4 | 添加样式和动画 | 1 小时 | 4.1.2 |
| 4.1.5 | 测试和优化 | 2 小时 | 全部 |

### 4.2 预计总时间

**1-2 天**

---

## 五、验收标准

### 5.1 功能验收

- [ ] 思考过程与最终答案分离展示
- [ ] 点击可展开/收缩思考过程
- [ ] 思考过程默认展开
- [ ] 支持 Markdown 渲染
- [ ] 视觉上清晰区分思考过程和答案
- [ ] 兼容不支持推理的模型

### 5.2 视觉验收

- [ ] 思考过程区域有明显标识
- [ ] 展开/收缩有平滑动画
- [ ] 加载状态显示正确
- [ ] 移动端适配良好

### 5.3 兼容性验收

- [ ] 豆包模型正常工作
- [ ] Llama 3.1 正常工作
- [ ] DeepSeek R1 正常工作（显示思考过程）
- [ ] 旧版前端兼容

---

## 六、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 推理内容提取失败 | 中 | 添加多种提取方式备选 |
| SSE 格式兼容问题 | 高 | 保持向后兼容 |
| 前端渲染性能 | 低 | 使用 DocumentFragment |

---

## 七、下一步行动

1. **评审本方案**: 请审阅并提出修改意见
2. **确认后开始实施**: 按计划推进开发
3. **测试验证**: 确保各模型正常工作

---

**文档结束**

请审阅此方案，确认后我将立即开始实施。
