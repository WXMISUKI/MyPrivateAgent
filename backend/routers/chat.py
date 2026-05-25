from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Annotated
import asyncio
import json
import logging

try:
    from agent_server.dependencies import get_current_user, get_db
    from agent_server.http import build_error_event, build_sse_event
    from models import User
    from schemas import ChatRequest, ChatResponse, ModelInfo
    from services.chat_service import (
        collect_orchestrator_response,
        collect_scheduled_orchestrator_response,
        get_or_create_conversation,
        maybe_complete_plan_after_chat,
        maybe_mark_plan_handoff_executing,
        maybe_start_plan_for_chat,
        merge_chat_execution_context,
        is_runtime_waiting_approval_event,
        RuntimeApprovalRequired,
        record_learning_if_possible,
        save_assistant_message,
        stream_scheduled_orchestrator_events,
        stream_orchestrator_events,
    )
    from services.runtime_surface_service import get_runtime_surface_service
    from orchestrator import get_orchestrator
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_server.dependencies import get_current_user, get_db
    from backend.agent_server.http import build_error_event, build_sse_event
    from backend.models import User
    from backend.schemas import ChatRequest, ChatResponse, ModelInfo
    from backend.services.chat_service import (
        collect_orchestrator_response,
        collect_scheduled_orchestrator_response,
        get_or_create_conversation,
        maybe_complete_plan_after_chat,
        maybe_mark_plan_handoff_executing,
        maybe_start_plan_for_chat,
        merge_chat_execution_context,
        is_runtime_waiting_approval_event,
        RuntimeApprovalRequired,
        record_learning_if_possible,
        save_assistant_message,
        stream_scheduled_orchestrator_events,
        stream_orchestrator_events,
    )
    from backend.services.runtime_surface_service import get_runtime_surface_service
    from backend.orchestrator import get_orchestrator

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["对话"])


def _prepare_chat_context(
    db: Session,
    user_id: int,
    conversation_id: int,
) -> tuple[dict | None, dict | None]:
    """Run plan lifecycle checks and return (started_plan_state, execution_context)."""
    started_plan_state = maybe_start_plan_for_chat(db=db, user_id=user_id, conversation_id=conversation_id)
    execution_context = None
    if started_plan_state:
        execution_context = started_plan_state.get("execution_context")

    executing_plan_state = maybe_mark_plan_handoff_executing(db=db, user_id=user_id, conversation_id=conversation_id)
    if executing_plan_state:
        execution_context = executing_plan_state.get("execution_context") or execution_context

    return started_plan_state, execution_context


# ============ API 路由 ============

@router.get("/models", response_model=list[ModelInfo])
def get_models():
    """获取可用模型列表"""
    return get_runtime_surface_service().list_models()


@router.post("/chat")
def chat(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """流式对话"""
    conversation, history_messages = get_or_create_conversation(
        request=request,
        current_user=current_user,
        db=db,
    )

    # 获取请求中的模型名称（如果有）
    model_name = request.model_name if request.model_name else conversation.model_name

    logger.info(f"[聊天] 会话ID: {request.conversation_id}")
    logger.info(f"[聊天] 使用模型: {model_name}")
    logger.info(f"[聊天] 用户消息: {request.message[:100]}...")
    logger.info(f"[聊天] 请求对象: {request}")
    logger.info(f"[聊天] 请求类型: {type(request)}")

    # 获取推理显示设置
    show_reasoning = getattr(request, 'show_reasoning', False)
    current_user_id = current_user.id if hasattr(current_user, 'id') else None

    # 使用新的协调器处理消息
    orchestrator = get_orchestrator(
        conversation_id=conversation.id,
        show_reasoning=show_reasoning
    )

    async def generate():
        """异步生成器 - 实现真正的流式输出"""
        try:
            logger.info(f"[Chat] 开始流式处理，会话ID: {request.conversation_id}")

            full_response = ""
            actual_content = ""
            pending_done_event = None
            execution_context = (
                request.execution_context.model_dump(exclude_none=True)
                if request.execution_context is not None
                else None
            )

            started_plan_state = maybe_start_plan_for_chat(
                db=db,
                user_id=current_user.id,
                conversation_id=conversation.id,
            )

            # 首先发送 conversation_id 给前端
            yield build_sse_event({"type": "conversation_id", "conversation_id": conversation.id})
            if started_plan_state:
                for event in started_plan_state.get("events", []):
                    yield build_sse_event(event)
                execution_context = merge_chat_execution_context(
                    execution_context,
                    started_plan_state.get("execution_context"),
                )
                if started_plan_state.get("blocked"):
                    blocked_message = started_plan_state.get("blocked_message") or "当前步骤因能力依赖不满足而被阻塞。"
                    yield build_sse_event({"type": "content", "content": blocked_message})
                    saved_message = save_assistant_message(db, conversation.id, blocked_message)
                    done_event = {"type": "done", "content": blocked_message}
                    saved_message_id = getattr(saved_message, "id", None)
                    if saved_message_id is not None:
                        done_event["message_id"] = saved_message_id
                    yield build_sse_event(done_event)
                    return

            executing_plan_state = maybe_mark_plan_handoff_executing(
                db=db,
                user_id=current_user.id,
                conversation_id=conversation.id,
            )
            if executing_plan_state:
                for event in executing_plan_state.get("events", []):
                    yield build_sse_event(event)
                execution_context = merge_chat_execution_context(
                    execution_context,
                    executing_plan_state.get("execution_context"),
                )

            try:
                stream_fn = stream_scheduled_orchestrator_events if execution_context and execution_context.get("scheduler_mode") == "fan_out" else stream_orchestrator_events
                stream_kwargs = {
                    "orchestrator": orchestrator,
                    "user_message": request.message,
                    "model_name": model_name,
                    "execution_context": execution_context,
                    "db": db,
                    "user_id": current_user.id,
                    "conversation_id": conversation.id,
                }
                if stream_fn is stream_scheduled_orchestrator_events:
                    stream_kwargs.update({})

                queue: asyncio.Queue = asyncio.Queue()
                stream_done = object()

                async def pump_stream():
                    try:
                        async for chunk, actual_content_snapshot in stream_fn(**stream_kwargs):
                            await queue.put(("chunk", chunk, actual_content_snapshot))
                    except Exception as pump_error:
                        await queue.put(("error", pump_error, None))
                    finally:
                        await queue.put(("done", stream_done, None))

                pump_task = asyncio.create_task(pump_stream())
                try:
                    while True:
                        try:
                            event_kind, event_payload, actual_content_snapshot = await asyncio.wait_for(queue.get(), timeout=12.0)
                        except asyncio.TimeoutError:
                            yield build_sse_event({
                                "type": "status",
                                "status_kind": "execution_progress",
                                "phase": "heartbeat",
                                "content": "仍在整理结果，请稍候。",
                            })
                            continue

                        if event_kind == "done":
                            break
                        if event_kind == "error":
                            raise event_payload

                        chunk = event_payload

                        full_response += chunk
                        actual_content = actual_content_snapshot

                        try:
                            parsed_chunk = json.loads(chunk)
                        except (json.JSONDecodeError, TypeError):
                            parsed_chunk = None

                        if isinstance(parsed_chunk, dict):
                            chunk_type = parsed_chunk.get("type")
                            payload = parsed_chunk.get("payload")
                            if not chunk_type and isinstance(payload, dict):
                                chunk_type = payload.get("type")
                            if chunk_type == "done":
                                pending_done_event = parsed_chunk
                                continue

                        yield build_sse_event(chunk)
                finally:
                    if not pump_task.done():
                        pump_task.cancel()
                        try:
                            await pump_task
                        except asyncio.CancelledError:
                            pass

            except Exception as e:
                logger.error(f"[Chat] 处理消息时出错: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                yield build_error_event(str(e))
                return

            logger.info(
                f"[Chat] 流式处理完成，原始流长度: {len(full_response)}, 最终内容长度: {len(actual_content)}"
            )

            if actual_content:
                saved_message = save_assistant_message(db, conversation.id, actual_content)
                saved_message_id = getattr(saved_message, "id", None)
                waiting_approval = bool(pending_done_event and is_runtime_waiting_approval_event(pending_done_event))

                completed_plan_payload = None
                if not waiting_approval:
                    completed_plan_payload = maybe_complete_plan_after_chat(
                        db=db,
                        user_id=current_user.id,
                        conversation_id=conversation.id,
                        assistant_content=actual_content,
                    )

                if pending_done_event:
                    if saved_message_id is not None:
                        pending_done_event["message_id"] = saved_message_id
                        payload = pending_done_event.get("payload")
                        if isinstance(payload, dict):
                            payload["message_id"] = saved_message_id
                    yield build_sse_event(pending_done_event)
                else:
                    fallback_done_event = {"type": "done", "content": actual_content}
                    if saved_message_id is not None:
                        fallback_done_event["message_id"] = saved_message_id
                    yield build_sse_event(fallback_done_event)

                if completed_plan_payload:
                    yield build_sse_event(completed_plan_payload)

                logger.info(f"[Chat] AI 响应已保存到数据库")

                if not waiting_approval:
                    record_learning_if_possible(
                        db=db,
                        user_message=request.message,
                        assistant_content=actual_content,
                        user_id=current_user_id,
                    )
            else:
                logger.warning(f"[Chat] AI 响应为空")
                if pending_done_event:
                    yield build_sse_event(pending_done_event)
                else:
                    fallback_message = "本次未生成有效回复，请重试"
                    saved_message = save_assistant_message(db, conversation.id, fallback_message)
                    fallback_done_event = {"type": "done", "content": fallback_message}
                    saved_message_id = getattr(saved_message, "id", None)
                    if saved_message_id is not None:
                        fallback_done_event["message_id"] = saved_message_id
                    yield build_sse_event({"type": "content", "content": fallback_message})
                    yield build_sse_event(fallback_done_event)

        except Exception as e:
            logger.error(f"[Chat] 处理错误: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            yield build_error_event(str(e))

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.post("/chat/non-stream")
async def chat_non_stream(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """非流式对话，复用统一的 Orchestrator 执行链。"""
    logger.info(f"[Non-Stream Chat] 开始处理")
    conversation, _ = get_or_create_conversation(
        request=request,
        current_user=current_user,
        db=db,
    )

    # 使用前端传递的模型名称，如果没传则使用会话中存储的模型
    model_name = request.model_name or conversation.model_name
    show_reasoning = getattr(request, 'show_reasoning', False)

    orchestrator = get_orchestrator(
        conversation_id=conversation.id,
        show_reasoning=show_reasoning,
    )
    started_plan_state, execution_context = _prepare_chat_context(
        db=db, user_id=current_user.id, conversation_id=conversation.id,
    )
    execution_context = merge_chat_execution_context(
        request.execution_context.model_dump(exclude_none=True) if request.execution_context is not None else None,
        execution_context,
    )
    if started_plan_state and started_plan_state.get("blocked"):
        blocked_message = started_plan_state.get("blocked_message") or "当前步骤因能力依赖不满足而被阻塞。"
        save_assistant_message(db, conversation.id, blocked_message)
        return ChatResponse(message=blocked_message, conversation_id=conversation.id)

    waiting_approval = False
    try:
        if execution_context and execution_context.get("scheduler_mode") == "fan_out":
            ai_response = await collect_scheduled_orchestrator_response(
                orchestrator=orchestrator,
                db=db,
                user_id=current_user.id,
                conversation_id=conversation.id,
                user_message=request.message,
                model_name=model_name,
                execution_context=execution_context,
            )
        else:
            ai_response = await collect_orchestrator_response(
                orchestrator=orchestrator,
                user_message=request.message,
                model_name=model_name,
                execution_context=execution_context,
                db=db,
                user_id=current_user.id,
                conversation_id=conversation.id,
            )
    except RuntimeApprovalRequired as approval:
        ai_response = approval.message
        waiting_approval = True
    except Exception as e:
        logger.error(f"[Non-Stream Chat] 模型调用失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模型调用失败: {str(e)}"
        )
    
    logger.info(f"[Non-Stream Chat] 模型返回: {ai_response[:100] if ai_response else '空'}...")

    save_assistant_message(db, conversation.id, ai_response)
    if not waiting_approval:
        maybe_complete_plan_after_chat(
            db=db,
            user_id=current_user.id,
            conversation_id=conversation.id,
            assistant_content=ai_response,
        )
        record_learning_if_possible(
            db=db,
            user_message=request.message,
            assistant_content=ai_response,
            user_id=current_user.id if hasattr(current_user, "id") else None,
        )
    
    logger.info(f"[Non-Stream Chat] 完成")

    return ChatResponse(message=ai_response, conversation_id=conversation.id)
