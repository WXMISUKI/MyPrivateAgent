import unittest
import shutil
import uuid
from pathlib import Path
from types import SimpleNamespace

from backend.services.skill_runtime_service import SkillRuntimeService


class SkillRuntimeServiceTests(unittest.TestCase):
    def _make_temp_root(self) -> Path:
        base_dir = Path(__file__).resolve().parent / ".tmp"
        base_dir.mkdir(parents=True, exist_ok=True)
        root = base_dir / f"skill-runtime-{uuid.uuid4().hex}"
        root.mkdir(parents=True, exist_ok=True)
        return root

    def test_build_runtime_context_selects_matching_skill_by_role_and_message(self):
        root = self._make_temp_root()
        try:
            frontend_dir = root / "frontend_ui"
            frontend_dir.mkdir()
            (frontend_dir / "SKILL.md").write_text(
                """---
name: Frontend UI Review
description: 适用于 Vue 页面、组件、交互与前端改造
tags:
- frontend
- vue
triggers:
- 页面
- 组件
agent_roles:
- frontend
---
## Overview
用于指导 Vue 页面、组件拆分、交互优化和样式调整。
""",
                encoding="utf-8",
            )
            backend_dir = root / "backend_api"
            backend_dir.mkdir()
            (backend_dir / "SKILL.md").write_text(
                """---
name: Backend API Review
description: 适用于接口、数据库与服务层修改
agent_roles:
- backend
---
## Overview
用于后端服务、接口和数据库治理。
""",
                encoding="utf-8",
            )

            skills = [
                SimpleNamespace(
                    id=1,
                    name="Frontend UI Review",
                    description="前端 Vue Skill",
                    storage_path=str(frontend_dir),
                ),
                SimpleNamespace(
                    id=2,
                    name="Backend API Review",
                    description="后端 Skill",
                    storage_path=str(backend_dir),
                ),
            ]

            service = SkillRuntimeService(max_skills=2)
            context = service.build_runtime_context(
                skills=skills,
                user_message="请继续完善当前 Vue 页面和组件交互",
                execution_context={"agent_role": "frontend"},
            )

            self.assertFalse(context.is_empty)
            self.assertEqual(context.metadata["selected_count"], 1)
            self.assertEqual(context.metadata["selected_skill_names"], ["Frontend UI Review"])
            self.assertIn("Frontend UI Review", context.system_prompt)
            self.assertEqual(context.selected_skills[0].score >= 1, True)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_build_runtime_context_skips_unmatched_skills(self):
        root = self._make_temp_root()
        try:
            docs_dir = root / "docs_skill"
            docs_dir.mkdir()
            (docs_dir / "SKILL.md").write_text(
                """---
name: Docs Skill
description: 只适用于说明文档整理
agent_roles:
- docs
---
## Overview
只在文档整理时使用。
""",
                encoding="utf-8",
            )

            service = SkillRuntimeService()
            context = service.build_runtime_context(
                skills=[
                    SimpleNamespace(
                        id=9,
                        name="Docs Skill",
                        description="文档 Skill",
                        storage_path=str(docs_dir),
                    )
                ],
                user_message="请修复接口超时问题",
                execution_context={"agent_role": "backend"},
            )

            self.assertTrue(context.is_empty)
            self.assertEqual(context.metadata["selected_count"], 0)
            self.assertEqual(context.skipped_skills[0]["reason"], "no_runtime_match")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_build_runtime_context_honors_manual_activation(self):
        root = self._make_temp_root()
        try:
            skill_dir = root / "manual_skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                """---
name: Manual Skill
description: 只能手工启用
activation: manual
priority: 9
triggers:
- 页面
---
## Overview
这是一个必须手工启用的 Skill。
""",
                encoding="utf-8",
            )

            service = SkillRuntimeService()
            context = service.build_runtime_context(
                skills=[SimpleNamespace(id=3, name="Manual Skill", description="manual", storage_path=str(skill_dir))],
                user_message="请优化页面交互",
                execution_context={"agent_role": "frontend"},
            )

            self.assertTrue(context.is_empty)
            self.assertEqual(context.metadata["selected_count"], 0)
            self.assertEqual(context.skipped_skills[0]["reason"], "no_runtime_match")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_build_runtime_context_role_only_requires_matching_role(self):
        root = self._make_temp_root()
        try:
            skill_dir = root / "backend_only"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                """---
name: Backend Strict Skill
description: 仅后端角色使用
activation: role_only
agent_roles:
- backend
---
## Overview
仅允许后端角色自动启用。
""",
                encoding="utf-8",
            )

            service = SkillRuntimeService()
            frontend_context = service.build_runtime_context(
                skills=[SimpleNamespace(id=4, name="Backend Strict Skill", description="backend only", storage_path=str(skill_dir))],
                user_message="请修复后端接口",
                execution_context={"agent_role": "frontend"},
            )
            backend_context = service.build_runtime_context(
                skills=[SimpleNamespace(id=4, name="Backend Strict Skill", description="backend only", storage_path=str(skill_dir))],
                user_message="请修复后端接口",
                execution_context={"agent_role": "backend"},
            )

            self.assertTrue(frontend_context.is_empty)
            self.assertFalse(backend_context.is_empty)
            self.assertEqual(backend_context.metadata["selected_skill_names"], ["Backend Strict Skill"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_build_runtime_context_resolves_domain_conflict_by_priority(self):
        root = self._make_temp_root()
        try:
            low_dir = root / "frontend_low"
            high_dir = root / "frontend_high"
            low_dir.mkdir()
            high_dir.mkdir()
            (low_dir / "SKILL.md").write_text(
                """---
name: Frontend Low Priority
description: 低优先级前端 Skill
domain: frontend-ui
priority: 1
agent_roles:
- frontend
triggers:
- 组件
---
## Overview
低优先级方案。
""",
                encoding="utf-8",
            )
            (high_dir / "SKILL.md").write_text(
                """---
name: Frontend High Priority
description: 高优先级前端 Skill
domain: frontend-ui
priority: 7
agent_roles:
- frontend
triggers:
- 组件
---
## Overview
高优先级方案。
""",
                encoding="utf-8",
            )

            service = SkillRuntimeService(max_skills=3)
            context = service.build_runtime_context(
                skills=[
                    SimpleNamespace(id=5, name="Frontend Low Priority", description="low", storage_path=str(low_dir)),
                    SimpleNamespace(id=6, name="Frontend High Priority", description="high", storage_path=str(high_dir)),
                ],
                user_message="请优化 Vue 组件结构",
                execution_context={"agent_role": "frontend"},
            )

            self.assertEqual(context.metadata["selected_count"], 1)
            self.assertEqual(context.metadata["selected_skill_names"], ["Frontend High Priority"])
            suppressed = [item for item in context.skipped_skills if item.get("reason") == "conflict_suppressed"]
            self.assertEqual(len(suppressed), 1)
            self.assertEqual(suppressed[0]["kept"], "Frontend High Priority")
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
