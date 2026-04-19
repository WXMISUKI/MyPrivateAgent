# MyPrivateAgent 自我改进能力设计方案

## 项目概述

基于 `self-improving-agent` 开源项目的核心思想，为 MyPrivateAgent 多智能体系统添加自我改进能力，使其能够：
- 自动记录错误和经验
- 从用户反馈中学习
- 定期复盘和优化
- 将学习成果转化为长期记忆

---

## 设计目标

### 核心目标
1. **自动错误记录** - 系统自动检测和记录错误
2. **经验自动总结** - 从对话中提取有价值经验
3. **长期记忆管理** - 将经验转化为可复用的知识
4. **每日自动复盘** - 定期分析和优化系统行为
5. **用户反馈学习** - 从用户纠正中提取正确知识

### 性能目标
- 错误检测准确率 > 90%
- 学习记录完整性 > 95%
- 知识应用效果提升 > 30%
- 用户满意度提升 > 20%

---

## 架构设计

### 系统架构图
```
┌─────────────────────────────────────────────────────────────┐
│                      用户对话层                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   智能检测与分析层                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 错误检测器   │  │ 机会识别器   │  │ 模式检测器   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   学习记录管理层                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 学习记录表   │  │ 错误记录表   │  │ 功能请求表   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   知识转化与提升层                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 经验总结器   │  │ 知识提取器   │  │ 技能生成器   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   长期记忆管理层                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 系统提示库   │  │ 最佳实践库   │  │ 知识图谱库   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   应用与反馈层                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 智能体优化   │  │ 提示注入     │  │ 效果评估     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 数据库设计

### 1. 学习记录表 (learnings)
```sql
CREATE TABLE learnings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    learning_id VARCHAR(50) UNIQUE NOT NULL,  -- 格式: LRN-YYYYMMDD-XXX
    category ENUM('correction', 'insight', 'knowledge_gap', 'best_practice') NOT NULL,
    priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    status ENUM('pending', 'in_progress', 'resolved', 'promoted', 'promoted_to_skill') DEFAULT 'pending',
    area VARCHAR(50),  -- frontend, backend, infra, tests, docs, config
    summary TEXT NOT NULL,
    details TEXT,
    suggested_action TEXT,
    source VARCHAR(50),  -- conversation, error, user_feedback
    related_files JSON,
    tags JSON,
    pattern_key VARCHAR(100),
    recurrence_count INT DEFAULT 1,
    first_seen DATETIME,
    last_seen DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    promoted_to TEXT NULL,  -- CLAUDE.md, AGENTS.md, etc.
    see_also JSON NULL,
    INDEX idx_category (category),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_area (area),
    INDEX idx_pattern_key (pattern_key)
);
```

### 2. 错误记录表 (errors)
```sql
CREATE TABLE errors (
    id INT PRIMARY KEY AUTO_INCREMENT,
    error_id VARCHAR(50) UNIQUE NOT NULL,  -- 格式: ERR-YYYYMMDD-XXX
    priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'high',
    status ENUM('pending', 'in_progress', 'resolved', 'wont_fix') DEFAULT 'pending',
    area VARCHAR(50),
    summary TEXT NOT NULL,
    error_message TEXT,
    context TEXT,
    suggested_fix TEXT,
    reproducible BOOLEAN DEFAULT FALSE,
    related_files JSON,
    see_also JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_area (area)
);
```

### 3. 功能请求表 (feature_requests)
```sql
CREATE TABLE feature_requests (
    id INT PRIMARY KEY AUTO_INCREMENT,
    feature_id VARCHAR(50) UNIQUE NOT NULL,  -- 格式: FEAT-YYYYMMDD-XXX
    priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    status ENUM('pending', 'in_progress', 'resolved', 'wont_fix') DEFAULT 'pending',
    area VARCHAR(50),
    requested_capability TEXT NOT NULL,
    user_context TEXT,
    complexity_estimate ENUM('simple', 'medium', 'complex'),
    suggested_implementation TEXT,
    frequency VARCHAR(20) DEFAULT 'first_time',  -- first_time, recurring
    related_features JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_area (area)
);
```

### 4. 系统提示表 (system_prompts)
```sql
CREATE TABLE system_prompts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    prompt_key VARCHAR(100) UNIQUE NOT NULL,
    prompt_type VARCHAR(50) NOT NULL,  -- behavior, workflow, tool_usage, etc.
    content TEXT NOT NULL,
    priority INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    area VARCHAR(50),
    tags JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_type (prompt_type),
    INDEX idx_active (is_active)
);
```

### 5. 最佳实践表 (best_practices)
```sql
CREATE TABLE best_practices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    practice_id VARCHAR(50) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    category VARCHAR(50),
    priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    code_example TEXT,
    trade_offs JSON,
    source_learning_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_priority (priority)
);
```

---

## 核心功能模块

### 1. 错误检测模块 (ErrorDetector)

**功能**:
- 自动检测对话中的错误模式
- 识别系统异常和失败情况
- 触发错误记录流程

**检测规则**:
```python
ERROR_PATTERNS = [
    "error:", "Error:", "ERROR:",
    "failed", "FAILED",
    "command not found",
    "No such file",
    "Permission denied",
    "fatal:",
    "Exception",
    "Traceback",
    "ModuleNotFoundError",
    "SyntaxError",
    "TypeError",
    "timeout",
    "connection failed"
]

USER_CORRECTION_PATTERNS = [
    "no, that's not right",
    "actually, it should be",
    "you're wrong about",
    "that's outdated",
    "纠正", "错误", "不对"
]
```

**实现**:
```python
class ErrorDetector:
    def __init__(self):
        self.error_patterns = ERROR_PATTERNS
        self.correction_patterns = USER_CORRECTION_PATTERNS
    
    def detect_errors(self, conversation_text: str) -> List[ErrorDetection]:
        """检测对话中的错误"""
        detections = []
        
        # 检测系统错误
        for pattern in self.error_patterns:
            if pattern.lower() in conversation_text.lower():
                detections.append(ErrorDetection(
                    type="system_error",
                    pattern=pattern,
                    confidence=0.9
                ))
        
        # 检测用户纠正
        for pattern in self.correction_patterns:
            if pattern.lower() in conversation_text.lower():
                detections.append(ErrorDetection(
                    type="user_correction",
                    pattern=pattern,
                    confidence=0.85
                ))
        
        return detections
```

---

### 2. 机会识别模块 (OpportunityIdentifier)

**功能**:
- 识别对话中的学习机会
- 提取有价值的经验和知识
- 识别可以优化的模式

**识别规则**:
```python
LEARNING_OPPORTUNITY_PATTERNS = [
    # 发现非显而易见的解决方案
    {"pattern": "investigation", "weight": 0.8},
    {"pattern": "调试", "weight": 0.9},
    
    # 发现更好的方法
    {"pattern": "improved", "weight": 0.7},
    {"pattern": "优化", "weight": 0.8},
    
    # 学习项目特定模式
    {"pattern": "convention", "weight": 0.9},
    {"pattern": "pattern", "weight": 0.7},
    
    # 用户主动分享知识
    {"pattern": "note that", "weight": 0.8},
    {"pattern": "注意", "weight": 0.9}
]
```

**实现**:
```python
class OpportunityIdentifier:
    def __init__(self):
        self.opportunity_patterns = LEARNING_OPPORTUNITY_PATTERNS
    
    def identify_opportunities(self, conversation: List[Message]) -> List[LearningOpportunity]:
        """识别学习机会"""
        opportunities = []
        
        for message in conversation:
            text = message.content.lower()
            for pattern in self.opportunity_patterns:
                if pattern["pattern"] in text:
                    opportunity = LearningOpportunity(
                        type=pattern["pattern"],
                        confidence=pattern["weight"],
                        message_id=message.id,
                        context=self._extract_context(message)
                    )
                    opportunities.append(opportunity)
        
        return opportunities
```

---

### 3. 模式检测模块 (PatternDetector)

**功能**:
- 检测重复出现的问题
- 识别周期性模式
- 统计模式频率

**实现**:
```python
class PatternDetector:
    def __init__(self):
        self.pattern_tracker = defaultdict(lambda: {"count": 0, "first_seen": None, "last_seen": None})
    
    def detect_recurring_patterns(self, learning: Learning) -> List[str]:
        """检测重复模式"""
        if learning.pattern_key:
            pattern_key = learning.pattern_key
            tracker = self.pattern_tracker[pattern_key]
            
            if tracker["count"] > 0:
                tracker["count"] += 1
                tracker["last_seen"] = datetime.now()
                return [pattern_key]
            else:
                tracker["count"] = 1
                tracker["first_seen"] = datetime.now()
                tracker["last_seen"] = datetime.now()
                return []
        
        return []
```

---

### 4. 学习记录模块 (LearningRecorder)

**功能**:
- 自动记录学习内容
- 分类和标记学习内容
- 关联相关文件和上下文

**API 接口**:
```python
POST /api/learnings/record
- 记录新的学习内容

GET /api/learnings
- 获取学习记录列表

GET /api/learnings/{learning_id}
- 获取单个学习记录

PUT /api/learnings/{learning_id}/resolve
- 标记学习记录为已解决

POST /api/learnings/{learning_id}/promote
- 将学习记录提升到系统提示

GET /api/learnings/stats
- 获取学习统计数据
```

---

### 5. 经验总结模块 (ExperienceSummarizer)

**功能**:
- 从对话中提取关键经验
- 生成结构化总结
- 关联相似学习内容

**实现**:
```python
class ExperienceSummarizer:
    def __init__(self, model_router):
        self.model_router = model_router
    
    async def summarize_experience(self, conversation: List[Message]) -> ExperienceSummary:
        """总结经验"""
        prompt = self._build_summary_prompt(conversation)
        model = self.model_router.get_model("doubao")
        response = await model.ainvoke([HumanMessage(content=prompt)])
        
        return ExperienceSummary(
            summary=response.content,
            category=self._infer_category(conversation),
            priority=self._infer_priority(conversation),
            suggested_action=self._extract_suggested_action(response.content)
        )
```

---

### 6. 知识提取模块 (KnowledgeExtractor)

**功能**:
- 从经验中提取可复用的知识
- 生成最佳实践文档
- 创建技能模板

**实现**:
```python
class KnowledgeExtractor:
    def __init__(self, model_router):
        self.model_router = model_router
    
    async def extract_knowledge(self, learning: Learning) -> Knowledge:
        """提取知识"""
        prompt = self._build_extraction_prompt(learning)
        model = self.model_router.get_model("doubao")
        response = await model.ainvoke([HumanMessage(content=prompt)])
        
        knowledge = Knowledge(
            title=self._extract_title(response.content),
            description=learning.details,
            category=learning.category,
            best_practice=response.content,
            code_example=self._extract_code_example(response.content)
        )
        
        return knowledge
```

---

### 7. 提示注入模块 (PromptInjector)

**功能**:
- 将系统提示注入到智能体对话中
- 动态调整提示内容
- 基于上下文优化提示

**实现**:
```python
class PromptInjector:
    def __init__(self):
        self.prompt_cache = {}
    
    def inject_prompts(self, conversation_id: int, context: Dict) -> List[str]:
        """注入系统提示"""
        prompts = []
        
        # 注入行为提示
        behavior_prompts = self._get_active_prompts("behavior", context)
        prompts.extend(behavior_prompts)
        
        # 注入工作流提示
        workflow_prompts = self._get_active_prompts("workflow", context)
        prompts.extend(workflow_prompts)
        
        # 注入工具使用提示
        tool_prompts = self._get_active_prompts("tool_usage", context)
        prompts.extend(tool_prompts)
        
        return prompts
    
    def _get_active_prompts(self, prompt_type: str, context: Dict) -> List[str]:
        """获取活跃提示"""
        # 从数据库或缓存中获取
        cache_key = f"{prompt_type}_{context.get('area', 'general')}"
        
        if cache_key in self.prompt_cache:
            return self.prompt_cache[cache_key]
        
        # 从数据库查询
        prompts = self._fetch_prompts_from_db(prompt_type, context)
        self.prompt_cache[cache_key] = prompts
        
        return prompts
```

---

## 实施计划

### 阶段 1: 基础设施（1-2 天）

**任务**:
1. 创建数据库表（learnings, errors, feature_requests, system_prompts, best_practices）
2. 实现数据库模型和 ORM 映射
3. 创建学习记录 API 接口
4. 实现基本的 CRUD 操作

**验收标准**:
- [ ] 数据库表创建成功
- [ ] API 接口可以正常调用
- [ ] 可以创建、查询、更新学习记录

---

### 阶段 2: 智能检测（2-3 天）

**任务**:
1. 实现 ErrorDetector 错误检测器
2. 实现 OpportunityIdentifier 机会识别器
3. 实现 PatternDetector 模式检测器
4. 集成到对话流程中

**验收标准**:
- [ ] 能够自动检测错误
- [ ] 能够识别学习机会
- [ ] 能够检测重复模式
- [ ] 检测准确率 > 90%

---

### 阶段 3: 记录管理（2-3 天）

**任务**:
1. 实现 LearningRecorder 学习记录器
2. 实现自动记录流程
3. 实现手动记录接口
4. 实现记录查询和统计

**验收标准**:
- [ ] 能够自动记录学习内容
- [ ] 能够手动添加学习记录
- [ ] 能够查询和统计学习记录
- [ ] 记录完整性 > 95%

---

### 阶段 4: 知识转化（2-3 天）

**任务**:
1. 实现 ExperienceSummarizer 经验总结器
2. 实现 KnowledgeExtractor 知识提取器
3. 实现知识提升机制
4. 创建技能模板

**验收标准**:
- [ ] 能够总结经验
- [ ] 能够提取知识
- [ ] 能够将知识提升到系统提示
- [ ] 知识应用效果提升 > 30%

---

### 阶段 5: 提示注入（2-3 天）

**任务**:
1. 实现 PromptInjector 提示注入器
2. 集成到智能体对话中
3. 实现动态提示调整
4. 实现效果评估

**验收标准**:
- [ ] 能够注入系统提示
- [ ] 能够动态调整提示
- [ ] 提示效果可评估
- [ ] 用户满意度提升 > 20%

---

### 阶段 6: 自动复盘（2-3 天）

**任务**:
1. 实现每日自动复盘
2. 实现学习记录审查
3. 实现优化建议生成
4. 实现效果跟踪

**验收标准**:
- [ ] 每日自动复盘
- [ ] 学习记录定期审查
- [ ] 优化建议准确
- [ ] 系统持续改进

---

### 阶段 7: 前端集成（1-2 天）

**任务**:
1. 创建学习记录管理界面
2. 显示学习统计信息
3. 实现手动记录功能
4. 实现学习记录查看和编辑

**验收标准**:
- [ ] 界面美观易用
- [ ] 功能完整
- [ ] 用户体验良好

---

### 阶段 8: 测试和优化（2-3 天）

**任务**:
1. 单元测试
2. 集成测试
3. 性能测试
4. 用户体验测试

**验收标准**:
- [ ] 所有测试通过
- [ ] 性能满足要求
- [ ] 用户体验良好

---

## 预期效果

### 量化指标
- **错误检测准确率**: > 90%
- **学习记录完整性**: > 95%
- **知识应用效果提升**: > 30%
- **用户满意度提升**: > 20%
- **系统响应速度**: < 2 秒

### 定性改进
1. **智能化提升** - 系统能够从错误中学习
2. **知识积累** - 逐步建立丰富的知识库
3. **自适应优化** - 根据学习结果自动调整
4. **用户体验** - 更准确、更智能的响应
5. **长期价值** - 持续改进，越来越智能

---

## 风险和挑战

### 技术风险
1. **检测准确性** - 可能存在误报和漏报
2. **知识质量** - 提取的知识可能不准确
3. **提示效果** - 注入的提示可能无效甚至有害
4. **性能影响** - 可能影响系统响应速度

### 应对措施
1. **持续优化** - 不断优化检测算法
2. **人工审核** - 重要知识需要人工审核
3. **A/B 测试** - 测试提示效果
4. **性能监控** - 实时监控系统性能

---

## 总结

本设计方案基于 `self-improving-agent` 的成功经验，为 MyPrivateAgent 多智能体系统添加自我改进能力。通过自动错误记录、经验总结、知识转化和提示注入，使系统能够持续学习和优化，越来越智能。

**预计实施时间**: 15-20 天
**预计工作量**: 8 个阶段
**预期效果**: 系统智能化水平显著提升

---

**是否同意此设计方案？确认后我将开始实施。**