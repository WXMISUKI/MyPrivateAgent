"""
危大工程识别 Agent 启动注册

将 Agent 注册到运行时，包含文档提取工具和意图识别。
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 意图关键词映射
INTENT_KEYWORDS = {
    "hazardous_project_recognition": [
        "危大工程", "超危大", "危大清单", "专项方案", "危险性较大",
        "hazardous", "危大识别", "工程清单识别", "危大工程识别",
    ],
}


def register_hazardous_agent():
    """注册危大工程识别 Agent。"""
    from ...runtime_plane.agents import Agent
    from ...runtime_plane.tools import tool, ToolRegistry
    from ...routers.agent_runtime import register_agent

    # 导入提示词
    prompts_dir = Path(__file__).parent / "prompts"
    system_prompt = (prompts_dir / "system.md").read_text(encoding="utf-8")
    task_prompt = (prompts_dir / "task.md").read_text(encoding="utf-8")
    full_instructions = f"{system_prompt}\n\n{task_prompt}"

    # 创建文档提取工具
    from .tools.document_extractor import extract_document_content, validate_json_output

    doc_tool = tool(extract_document_content)
    validate_tool = tool(validate_json_output)

    # 创建 Agent
    agent = Agent(
        name="hazardous_project_recognition",
        instructions=full_instructions,
        model="doubao",
        tools=[doc_tool, validate_tool],
        description="从 Excel/Word/CSV 文件中识别危大工程清单，匹配标准名称和类别，判定是否超危大。",
        metadata={
            "domain": "construction-safety",
            "intent_keywords": INTENT_KEYWORDS["hazardous_project_recognition"],
            "requires_file_upload": True,
            "supported_formats": [".doc", ".docx", ".xlsx", ".xls", ".csv"],
        },
    )

    register_agent(agent)
    logger.info("Registered agent: hazardous_project_recognition")
    return agent


def match_intent(user_input: str) -> str | None:
    """根据用户输入匹配意图，返回 agent_id 或 None。"""
    text = user_input.lower()
    for agent_id, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                return agent_id
    return None
