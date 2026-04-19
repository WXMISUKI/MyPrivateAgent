"""
提示注入模块
用于将系统提示注入到智能体对话中
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models import SystemPrompt, Area


class PromptInjector:
    """提示注入器"""
    
    def __init__(self):
        self.prompt_cache = {}
        self.cache_timeout = 300  # 缓存超时时间（秒）
    
    def inject_prompts(
        self,
        conversation_id: int,
        context: Dict,
        db: Session
    ) -> List[str]:
        """
        注入系统提示
        
        Args:
            conversation_id: 对话ID
            context: 上下文信息
            db: 数据库会话
            
        Returns:
            提示列表
        """
        prompts = []
        
        # 注入行为提示
        behavior_prompts = self._get_active_prompts("behavior", context, db)
        prompts.extend(behavior_prompts)
        
        # 注入工作流提示
        workflow_prompts = self._get_active_prompts("workflow", context, db)
        prompts.extend(workflow_prompts)
        
        # 注入工具使用提示
        tool_prompts = self._get_active_prompts("tool_usage", context, db)
        prompts.extend(tool_prompts)
        
        # 注入区域特定提示
        if context.get("area"):
            area_prompts = self._get_active_prompts("behavior", {"area": context["area"]}, db)
            prompts.extend(area_prompts)
        
        return prompts
    
    def _get_active_prompts(
        self,
        prompt_type: str,
        context: Dict,
        db: Session
    ) -> List[str]:
        """
        获取活跃提示
        
        Args:
            prompt_type: 提示类型
            context: 上下文信息
            db: 数据库会话
            
        Returns:
            提示内容列表
        """
        # 检查缓存
        cache_key = self._generate_cache_key(prompt_type, context)
        
        if cache_key in self.prompt_cache:
            cached_time, cached_prompts = self.prompt_cache[cache_key]
            
            # 检查缓存是否过期
            if (datetime.now() - cached_time).total_seconds() < self.cache_timeout:
                return cached_prompts
        
        # 从数据库查询
        query = db.query(SystemPrompt).filter(SystemPrompt.is_active == True)
        
        if prompt_type:
            query = query.filter(SystemPrompt.prompt_type == prompt_type)
        
        # 按优先级排序
        query = query.order_by(SystemPrompt.priority.desc())
        
        prompts = query.limit(20).all()
        
        # 转换为提示内容列表
        prompt_contents = [prompt.content for prompt in prompts]
        
        # 缓存结果
        self.prompt_cache[cache_key] = (datetime.now(), prompt_contents)
        
        return prompt_contents
    
    def _generate_cache_key(self, prompt_type: str, context: Dict) -> str:
        """
        生成缓存键
        
        Args:
            prompt_type: 提示类型
            context: 上下文信息
            
        Returns:
            缓存键
        """
        parts = [prompt_type]
        
        if context.get("area"):
            parts.append(context["area"])
        
        return "_".join(parts)
    
    def clear_cache(self):
        """清除缓存"""
        self.prompt_cache.clear()
    
    def inject_for_model(
        self,
        model_name: str,
        context: Dict,
        db: Session
    ) -> str:
        """
        为特定模型注入提示
        
        Args:
            model_name: 模型名称
            context: 上下文信息
            db: 数据库会话
            
        Returns:
            组合后的提示
        """
        # 获取所有相关提示
        prompts = self.inject_prompts(0, context, db)
        
        if not prompts:
            return ""
        
        # 组合提示
        combined_prompt = "\n\n".join([
            "# 系统提示\n",
            "\n".join(prompts),
            "\n# 以上是系统提示，请遵循这些指导\n"
        ])
        
        return combined_prompt
    
    def get_relevant_prompts(
        self,
        task_type: str,
        area: Optional[str],
        db: Session
    ) -> List[Dict]:
        """
        获取相关提示
        
        Args:
            task_type: 任务类型
            area: 区域
            db: 数据库会话
            
        Returns:
            相关提示列表
        """
        query = db.query(SystemPrompt).filter(
            SystemPrompt.is_active == True
        )
        
        # 按任务类型过滤
        if task_type:
            query = query.filter(
                SystemPrompt.prompt_type == task_type
            )
        
        # 按区域过滤
        if area:
            query = query.filter(
                SystemPrompt.area == Area[area.upper()]
            )
        
        # 按优先级排序
        query = query.order_by(SystemPrompt.priority.desc())
        
        prompts = query.limit(10).all()
        
        return [
            {
                "prompt_key": prompt.prompt_key,
                "prompt_type": prompt.prompt_type,
                "content": prompt.content,
                "priority": prompt.priority,
                "area": prompt.area.value if prompt.area else None,
                "tags": prompt.tags
            }
            for prompt in prompts
        ]


class PromptManager:
    """提示管理器"""
    
    def __init__(self):
        self.injector = PromptInjector()
    
    def add_system_prompt(
        self,
        prompt_key: str,
        prompt_type: str,
        content: str,
        area: Optional[str] = None,
        priority: int = 1,
        db: Session = Depends(None)
    ) -> Dict:
        """
        添加系统提示
        
        Args:
            prompt_key: 提示键
            prompt_type: 提示类型
            content: 提示内容
            area: 区域
            priority: 优先级
            db: 数据库会话
            
        Returns:
            创建的提示信息
        """
        try:
            system_prompt = SystemPrompt(
                prompt_key=prompt_key,
                prompt_type=prompt_type,
                content=content,
                priority=priority,
                area=Area[area.upper()] if area else None,
                tags=[]
            )
            
            db.add(system_prompt)
            db.commit()
            db.refresh(system_prompt)
            
            # 清除缓存
            self.injector.clear_cache()
            
            return {
                "success": True,
                "id": system_prompt.id,
                "prompt_key": system_prompt.prompt_key,
                "content": system_prompt.content
            }
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_prompt(
        self,
        prompt_key: str,
        is_active: Optional[bool] = None,
        content: Optional[str] = None,
        db: Session = Depends(None)
    ) -> Dict:
        """
        更新系统提示
        
        Args:
            prompt_key: 提示键
            is_active: 是否活跃
            content: 提示内容
            db: 数据库会话
            
        Returns:
            更新结果
        """
        try:
            prompt = db.query(SystemPrompt).filter(
                SystemPrompt.prompt_key == prompt_key
            ).first()
            
            if not prompt:
                return {
                    "success": False,
                    "error": f"提示 {prompt_key} 不存在"
                }
            
            if is_active is not None:
                prompt.is_active = is_active
            
            if content:
                prompt.content = content
            
            prompt.updated_at = datetime.now()
            
            db.commit()
            db.refresh(prompt)
            
            # 清除缓存
            self.injector.clear_cache()
            
            return {
                "success": True,
                "prompt_key": prompt.prompt_key,
                "is_active": prompt.is_active
            }
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_prompt(
        self,
        prompt_key: str,
        db: Session = Depends(None)
    ) -> Dict:
        """
        删除系统提示
        
        Args:
            prompt_key: 提示键
            db: 数据库会话
            
        Returns:
            删除结果
        """
        try:
            prompt = db.query(SystemPrompt).filter(
                SystemPrompt.prompt_key == prompt_key
            ).first()
            
            if not prompt:
                return {
                    "success": False,
                    "error": f"提示 {prompt_key} 不存在"
                }
            
            db.delete(prompt)
            db.commit()
            
            # 清除缓存
            self.injector.clear_cache()
            
            return {
                "success": True,
                "prompt_key": prompt_key
            }
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_all_prompts(
        self,
        db: Session,
        is_active: Optional[bool] = None,
        prompt_type: Optional[str] = None
    ) -> List[Dict]:
        """
        获取所有提示
        
        Args:
            db: 数据库会话
            is_active: 是否活跃过滤
            prompt_type: 提示类型过滤
            
        Returns:
            提示列表
        """
        query = db.query(SystemPrompt)
        
        if is_active is not None:
            query = query.filter(SystemPrompt.is_active == is_active)
        
        if prompt_type:
            query = query.filter(SystemPrompt.prompt_type == prompt_type)
        
        # 按优先级排序
        query = query.order_by(SystemPrompt.priority.desc())
        
        prompts = query.limit(100).all()
        
        return [
            {
                "id": prompt.id,
                "prompt_key": prompt.prompt_key,
                "prompt_type": prompt.prompt_type,
                "content": prompt.content,
                "priority": prompt.priority,
                "is_active": prompt.is_active,
                "area": prompt.area.value if prompt.area else None,
                "tags": prompt.tags,
                "created_at": prompt.created_at.isoformat(),
                "updated_at": prompt.updated_at.isoformat()
            }
            for prompt in prompts
        ]


# 全局单例
_prompt_manager_instance = None


def get_prompt_manager() -> PromptManager:
    """获取全局提示管理器实例"""
    global _prompt_manager_instance
    if _prompt_manager_instance is None:
        _prompt_manager_instance = PromptManager()
    return _prompt_manager_instance
