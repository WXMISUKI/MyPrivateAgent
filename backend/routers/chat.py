from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Annotated, Generator
import json
import asyncio
from datetime import datetime
import logging

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from langchain_core.tools import Tool
from pydantic import BaseModel
from typing import Literal, Any, Dict
from typing_extensions import TypedDict
from langchain_core.callbacks.base import BaseCallbackHandler

from database import get_db
from models import User, Conversation, Message, Skill
from schemas import ChatRequest, ChatResponse, ModelInfo
from auth import get_current_user
from config import OLLAMA_BASE_URL, DEFAULT_MODEL, AVAILABLE_MODELS, PROJECT_ROOT, ARK_API_KEY, ARK_BASE_URL, ARK_MODEL
import pytz
import os

# 导入协调器
from orchestrator import get_orchestrator

# 导入自学习模块
from learning_recorder import LearningRecorder


# ============ Skills 加载函数 ============
def load_enabled_skills() -> list:
    """加载所有已启用的 Skills"""
    from database import SessionLocal
    db = SessionLocal()
    try:
        skills = db.query(Skill).filter(Skill.is_enabled == 1).all()
        result = []
        for skill in skills:
            skill_md_path = os.path.join(skill.storage_path, "SKILL.md")
            content = ""
            if os.path.exists(skill_md_path):
                with open(skill_md_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            result.append({
                "name": skill.name,
                "description": skill.description,
                "content": content
            })
        return result
    finally:
        db.close()


def build_system_prompt_with_skills(skills: list) -> str:
    """构建包含 Skills 的系统提示"""
    if not skills:
        return ""
    
    skills_section = "\n\n## 可用的 Skills\n\n"
    for skill in skills:
        skills_section += f"### {skill['name']}\n"
        skills_section += f"描述: {skill['description']}\n\n"
    
    skills_section += "\n当用户请求与某个 Skill 相关时，请参考对应的 SKILL.md 文件内容来完成任务。\n"
    
    return skills_section

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["对话"])


# ============ LangChain Callback Handler ============

class DetailedLoggingHandler(BaseCallbackHandler):
    """自定义 callback handler 用于详细日志输出"""
    
    def on_chat_model_start(self, serialized, messages, **kwargs):
        logger.debug(f"[LangChain] ChatModel 开始处理消息")
        for msg in messages:
            logger.debug(f"[LangChain] 输入消息 - role: {msg.type}, content: {msg.content[:100]}...")
    
    def on_chat_model_end(self, response, **kwargs):
        logger.debug(f"[LangChain] ChatModel 处理完成")
        if hasattr(response, 'content'):
            logger.debug(f"[LangChain] 输出内容: {response.content[:100] if response.content else '空'}...")
    
    def on_chat_model_error(self, error, **kwargs):
        logger.error(f"[LangChain] ChatModel 错误: {error}")
    
    def on_chain_start(self, serialized, inputs, **kwargs):
        logger.debug(f"[LangGraph] Chain 开始 - {serialized.get('name', 'unknown')}")
        logger.debug(f"[LangGraph] 输入状态: {inputs}")
    
    def on_chain_end(self, outputs, **kwargs):
        logger.debug(f"[LangGraph] Chain 结束")
        logger.debug(f"[LangGraph] 输出状态: {outputs}")
    
    def on_chain_error(self, error, **kwargs):
        logger.error(f"[LangGraph] Chain 错误: {error}")
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        logger.debug(f"[LangGraph] Tool 开始 - {serialized.get('name', 'unknown')}")
        logger.debug(f"[LangGraph] Tool 输入: {input_str}")
    
    def on_tool_end(self, output, **kwargs):
        logger.debug(f"[LangGraph] Tool 结束")
        logger.debug(f"[LangGraph] Tool 输出: {output}")
    
    def on_tool_error(self, error, **kwargs):
        logger.error(f"[LangGraph] Tool 错误: {error}")


# 创建全局 callback handler
logging_handler = DetailedLoggingHandler()


# ============ LangGraph 相关 ============

class MessagesState(TypedDict):
    messages: list


# 不支持工具的模型列表（仅本地 Ollama 模型）
MODELS_WITHOUT_TOOLS = ["deepseek-r1:7b", "llava", "llama3.1"]

# 需要使用火山引擎 ARK API 的模型
MODELS_USING_ARK = ["doubao"]


# 工具定义
def search(query: str) -> str:
    """模拟搜索工具"""
    if "上海" in query.lower() or "shanghai" in query.lower():
        return "现在30度，有雾。"
    return "现在是35度，阳光明媚。"


def get_current_datetime() -> str:
    """获取当前日期时间"""
    timezone = pytz.timezone('Asia/Shanghai')
    now = datetime.now(timezone)
    weekday_map = {
        0: "星期一", 1: "星期二", 2: "星期三",
        3: "星期四", 4: "星期五", 5: "星期六", 6: "星期日"
    }
    return f"{now.strftime('%Y-%m-%d')} {now.strftime('%H:%M:%S')} {weekday_map[now.weekday()]}"


# 使用 langchain_core.tools.Tool 创建工具列表
tools = [
    Tool(
        name="search",
        func=search,
        description="用于搜索信息，特别是天气查询"
    ),
    Tool(
        name="get_current_datetime",
        func=get_current_datetime,
        description="获取当前的日期和时间"
    )
]


# 自定义工具节点函数（替代 ToolNode）
def tool_node(state: MessagesState) -> dict:
    """执行工具调用并返回结果"""
    messages = state["messages"]
    last_message = messages[-1]

    # 检查最后一条消息是否包含工具调用
    tool_calls = getattr(last_message, 'tool_calls', [])
    if not tool_calls:
        return {"messages": []}

    tool_messages = []
    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})

        # 执行工具
        tool_result = None
        for tool in tools:
            if tool.name == tool_name:
                try:
                    tool_result = tool.func(**tool_args)
                except Exception as e:
                    tool_result = f"工具执行错误: {str(e)}"
                break

        if tool_result is not None:
            tool_messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call.get("id", ""),
                )
            )

    return {"messages": tool_messages}


def should_continue(state: MessagesState) -> str:
    """决定是否继续执行工具"""
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return END


def create_graph(model_name: str):
    """为每个模型创建独立的图（无缓存版，每次从数据库读取历史）"""
    # 加载已启用的 Skills
    enabled_skills = load_enabled_skills()
    skills_prompt = build_system_prompt_with_skills(enabled_skills)

    # 创建模型，启用 verbose 详细日志
    model = ChatOllama(
        model=model_name,
        temperature=0.7,
        base_url=OLLAMA_BASE_URL,
        verbose=True,  # 启用 LangChain 详细日志
        callbacks=[logging_handler]  # 添加自定义 callback
    )

    # 检查模型是否支持工具调用
    if model_name not in MODELS_WITHOUT_TOOLS:
        # 绑定工具到模型
        model_with_tools = model.bind_tools(tools)

        def call_model(state: MessagesState):
            messages = state["messages"]

            # 如果有启用的 Skills，在用户消息前插入系统提示
            if skills_prompt and messages:
                from langchain_core.messages import SystemMessage
                # 检查是否已有系统消息
                if not isinstance(messages[0], SystemMessage):
                    system_msg = SystemMessage(content=f"你是一个智能助手。{skills_prompt}")
                    messages = [system_msg] + messages

            logger.info(f"[LangGraph] 调用模型（带工具）: {model_name}, 消息数量: {len(messages)}")
            response = model_with_tools.invoke(messages)
            logger.info(f"[LangGraph] 模型返回: {response.content[:100] if response.content else '空'}...")
            if hasattr(response, 'tool_calls') and response.tool_calls:
                logger.info(f"[LangGraph] 工具调用: {response.tool_calls}")
            return {"messages": [response]}

        # 创建包含工具调用的图
        workflow = StateGraph(MessagesState)
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", tool_node)

        workflow.set_entry_point("agent")
        workflow.add_conditional_edges("agent", should_continue)
        workflow.add_edge("tools", "agent")
    else:
        # 不支持工具调用的模型，使用简单对话
        def call_model(state: MessagesState):
            messages = state["messages"]

            # 如果有启用的 Skills，在用户消息前插入系统提示
            if skills_prompt and messages:
                from langchain_core.messages import SystemMessage
                # 检查是否已有系统消息
                if not isinstance(messages[0], SystemMessage):
                    system_msg = SystemMessage(content=f"你是一个智能助手。{skills_prompt}")
                    messages = [system_msg] + messages

            logger.info(f"[LangGraph] 调用模型（无工具）: {model_name}, 消息数量: {len(messages)}")
            response = model.invoke(messages)
            logger.info(f"[LangGraph] 模型返回: {response.content[:100] if response.content else '空'}...")
            return {"messages": [response]}

        # 创建简单对话图
        workflow = StateGraph(MessagesState)
        workflow.add_node("agent", call_model)
        workflow.set_entry_point("agent")
        workflow.add_edge("agent", END)

    # 不使用 MemorySaver，完全依赖数据库存储历史消息
    return workflow.compile(debug=True)


# 缓存已创建的图
graph_cache = {}


def clear_graph_cache(model_name: str = None):
    """清除图缓存"""
    global graph_cache
    if model_name:
        # 清除指定模型的缓存
        if model_name in graph_cache:
            del graph_cache[model_name]
    else:
        # 清除所有缓存
        graph_cache = {}


def get_graph(model_name: str):
    """获取或创建图"""
    if model_name not in graph_cache:
        graph_cache[model_name] = create_graph(model_name)
    return graph_cache[model_name]


# ============ API 路由 ============

@router.get("/models", response_model=list[ModelInfo])
def get_models():
    """获取可用模型列表"""
    return AVAILABLE_MODELS


@router.post("/chat")
def chat(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """流式对话"""
    conversation = None

    if request.conversation_id:
        # 验证会话归属
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id
        ).first()

    if not conversation:
        # 创建新会话
        conversation = Conversation(
            user_id=current_user.id,
            title=request.message[:30] + ("..." if len(request.message) > 30 else ""),
            model_name=request.model_name or "doubao"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # 获取历史消息
    history_messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at).all()

    # 构建消息列表
    messages = []
    for msg in history_messages:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))

    # 添加当前用户消息
    user_message = HumanMessage(content=request.message)
    messages.append(user_message)

    # 保存用户消息到数据库
    db.add(Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    ))

    # 更新会话时间
    conversation.updated_at = datetime.now()

    # 如果是第一条消息，更新标题
    if len(history_messages) == 0:
        # 使用用户消息的前20个字符作为标题
        conversation.title = request.message[:20] + ("..." if len(request.message) > 20 else "")

    db.commit()

    # 获取请求中的模型名称（如果有）
    model_name = request.model_name if request.model_name else conversation.model_name

    # 如果模型变更了，更新数据库
    if request.model_name and request.model_name != conversation.model_name:
        conversation.model_name = request.model_name
        db.commit()
        # 清除旧模型缓存
        clear_graph_cache(conversation.model_name)

    logger.info(f"[聊天] 会话ID: {request.conversation_id}")
    logger.info(f"[聊天] 使用模型: {model_name}")
    logger.info(f"[聊天] 用户消息: {request.message[:100]}...")
    logger.info(f"[聊天] 请求对象: {request}")
    logger.info(f"[聊天] 请求类型: {type(request)}")

    # 获取推理显示设置
    show_reasoning = getattr(request, 'show_reasoning', False)

    # 使用新的协调器处理消息
    orchestrator = get_orchestrator(
        conversation_id=request.conversation_id,
        show_reasoning=show_reasoning
    )

    async def generate():
        """异步生成器 - 实现真正的流式输出"""
        try:
            logger.info(f"[Chat] 开始流式处理，会话ID: {request.conversation_id}")

            full_response = ""
            actual_content = ""

            # 首先发送 conversation_id 给前端
            yield f"data: {json.dumps({'type': 'conversation_id', 'conversation_id': conversation.id})}\n\n"

            try:
                async for chunk in orchestrator.process_message(
                    user_message=request.message,
                    selected_model=model_name
                ):
                    full_response += chunk

                    try:
                        parsed = json.loads(chunk)
                        msg_type = parsed.get('type', '')
                        if msg_type == 'content' or msg_type == 'answer':
                            actual_content += parsed.get('content', '') or parsed.get('answer', '')
                    except (json.JSONDecodeError, TypeError):
                        if chunk.strip():
                            actual_content += chunk

                    yield f"data: {chunk}\n\n"

            except Exception as e:
                logger.error(f"[Chat] 处理消息时出错: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
                return

            logger.info(f"[Chat] 流式处理完成，响应长度: {len(full_response)}")

            if actual_content:
                db.add(Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=actual_content
                ))
                db.commit()
                logger.info(f"[Chat] AI 响应已保存到数据库")

                try:
                    recorder = LearningRecorder()
                    conversation_text = f"用户: {request.message}\n助手: {actual_content}"
                    records = recorder.record_from_conversation(
                        conversation_text=conversation_text,
                        db=db,
                        user_id=current_user.id,
                        area=None
                    )
                    if records:
                        logger.info(f"[Chat] 自学习：记录了 {len(records)} 条学习内容")
                except Exception as e:
                    logger.error(f"[Chat] 自学习记录失败: {e}")
            else:
                logger.warning(f"[Chat] AI 响应为空")

        except Exception as e:
            logger.error(f"[Chat] 处理错误: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.post("/chat/non-stream")
def chat_non_stream(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """非流式对话（备用）"""
    logger.info(f"[Non-Stream Chat] 开始处理")

    conversation = None

    if request.conversation_id:
        # 验证会话归属
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id
        ).first()

    if not conversation:
        # 创建新会话
        conversation = Conversation(
            user_id=current_user.id,
            title=request.message[:30] + ("..." if len(request.message) > 30 else ""),
            model_name=request.model_name or "doubao"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # 获取历史消息
    history_messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at).all()

    # 构建消息列表
    messages = []
    for msg in history_messages:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))

    # 添加当前用户消息
    messages.append(HumanMessage(content=request.message))
    
    logger.debug(f"[Non-Stream Chat] 消息列表: {len(messages)} 条")

    # 保存用户消息到数据库
    db.add(Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    ))

    # 更新会话时间
    conversation.updated_at = datetime.now()

    # 如果是第一条消息，更新标题
    if len(history_messages) == 0:
        conversation.title = request.message[:20] + ("..." if len(request.message) > 20 else "")

    db.commit()

    # 使用前端传递的模型名称，如果没传则使用会话中存储的模型
    model_name = request.model_name or conversation.model_name

    # 加载 skills prompt
    enabled_skills = load_enabled_skills()
    skills_prompt = build_system_prompt_with_skills(enabled_skills)

    # 对于不支持工具调用的模型，使用简化处理
    try:
        if model_name in MODELS_WITHOUT_TOOLS:
            logger.info(f"[Non-Stream Chat] 使用简化模式（无工具）: {model_name}")

            # 直接调用模型，不使用 LangGraph
            from langchain_ollama import ChatOllama
            simple_model = ChatOllama(
                model=model_name,
                temperature=0.7,
                base_url=OLLAMA_BASE_URL,
            )

            # 构建消息列表（不添加 Skills 提示，避免模型产生不必要的回复）
            chat_messages = []
            for msg in messages:
                chat_messages.append(msg)

            logger.info(f"[Non-Stream Chat] 直接调用模型，消息数量: {len(chat_messages)}")
            response = simple_model.invoke(chat_messages)
            ai_response = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"[Non-Stream Chat] 模型返回: {ai_response[:100] if ai_response else '空'}...")
        elif model_name in MODELS_USING_ARK:
            # 豆包模型使用火山引擎 ARK API
            logger.info(f"[Non-Stream Chat] 使用 ARK API 模式: {model_name}")

            from langchain_openai import ChatOpenAI
            ark_model = ChatOpenAI(
                base_url=ARK_BASE_URL,
                model=ARK_MODEL,
                api_key=ARK_API_KEY,
                temperature=0.7,
                max_tokens=2048,
                timeout=30,
            )

            # 构建消息列表（不添加 Skills 提示，避免模型产生不必要的回复）
            chat_messages = []
            for msg in messages:
                chat_messages.append(msg)

            logger.info(f"[Non-Stream Chat] 通过 ARK API 调用豆包，消息数量: {len(chat_messages)}")
            response = ark_model.invoke(chat_messages)
            ai_response = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"[Non-Stream Chat] 模型返回: {ai_response[:100] if ai_response else '空'}...")
        else:
            # 支持工具调用的模型，使用 LangGraph
            graph = get_graph(model_name)
            logger.info(f"[Non-Stream Chat] 调用模型: {model_name}")
            result = graph.invoke({"messages": messages})
            ai_response = result["messages"][-1].content
    except Exception as e:
        logger.error(f"[Non-Stream Chat] 模型调用失败: {e}", exc_info=True)
        import traceback
        logger.error(f"[Non-Stream Chat] 详细错误: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模型调用失败: {str(e)}"
        )
    
    logger.info(f"[Non-Stream Chat] 模型返回: {ai_response[:100] if ai_response else '空'}...")

    # 保存 AI 响应
    db.add(Message(
        conversation_id=conversation.id,
        role="assistant",
        content=ai_response
    ))
    db.commit()
    
    logger.info(f"[Non-Stream Chat] 完成")

    return ChatResponse(message=ai_response, conversation_id=conversation.id)
