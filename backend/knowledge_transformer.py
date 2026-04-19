"""
知识转化模块
用于从学习记录中提取可复用的知识和最佳实践
"""
from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy.orm import Session

from models import Learning, BestPractice, SystemPrompt
from model_router import get_model_router
from langchain_core.messages import HumanMessage, AIMessage


class ExperienceSummarizer:
    """经验总结器"""
    
    def __init__(self):
        self.model_router = get_model_router()
    
    async def summarize_learning(
        self,
        learning: Learning,
        db: Session
    ) -> Dict:
        """
        总结学习记录
        
        Args:
            learning: 学习记录
            db: 数据库会话
            
        Returns:
            总结结果
        """
        try:
            # 构建总结提示
            prompt = f"""请总结以下学习记录，提取关键信息：

学习记录：
{learning.summary}

详细内容：
{learning.details}

建议操作：
{learning.suggested_action}

请提供以下格式的总结：
1. 核心问题：一句话描述主要问题
2. 根本原因：分析问题产生的根本原因
3. 解决方案：具体的解决步骤
4. 预防措施：如何避免类似问题再次发生
5. 相关领域：涉及的系统区域
"""
            
            # 调用模型
            try:
                model = self.model_router.get_model("doubao")
            except ValueError:
                # 豆包模型未配置，降级使用本地模型
                try:
                    model = self.model_router.get_model("llama3.1")
                except ValueError:
                    model = self.model_router.get_model("deepseek-r1:7b")
            
            response = await model.ainvoke([HumanMessage(content=prompt)])
            
            # 解析总结
            summary_text = response.content
            
            return {
                "learning_id": learning.learning_id,
                "summary_text": summary_text,
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "learning_id": learning.learning_id,
                "error": str(e),
                "created_at": datetime.now().isoformat()
            }
    
    async def batch_summarize(
        self,
        limit: int = 10,
        db: Session = Depends(None)
    ) -> List[Dict]:
        """
        批量总结学习记录
        
        Args:
            limit: 限制数量
            db: 数据库会话
            
        Returns:
            总结结果列表
        """
        # 获取未总结的学习记录
        learnings = db.query(Learning).filter(
            Learning.status == "pending"
        ).limit(limit).all()
        
        results = []
        
        for learning in learnings:
            result = await self.summarize_learning(learning, db)
            results.append(result)
        
        return results


class KnowledgeExtractor:
    """知识提取器"""
    
    def __init__(self):
        self.model_router = get_model_router()
    
    async def extract_knowledge(
        self,
        learning: Learning,
        db: Session
    ) -> Dict:
        """
        从学习记录中提取知识
        
        Args:
            learning: 学习记录
            db: 数据库会话
            
        Returns:
            提取的知识
        """
        try:
            # 构建知识提取提示
            prompt = f"""从以下学习记录中提取可复用的知识：

学习记录：
{learning.summary}

详细内容：
{learning.details}

建议操作：
{learning.suggested_action}

请提取以下信息：
1. 知识标题：简洁的标题
2. 知识描述：详细描述这个知识
3. 适用场景：在什么情况下可以使用这个知识
4. 代码示例：如果有相关的代码示例
5. 注意事项：使用时需要注意什么
6. 相关文件：相关的文件或模块

请以结构化的格式返回。
"""
            
            # 调用模型
            try:
                model = self.model_router.get_model("doubao")
            except ValueError:
                # 豆包模型未配置，降级使用本地模型
                try:
                    model = self.model_router.get_model("llama3.1")
                except ValueError:
                    model = self.model_router.get_model("deepseek-r1:7b")
            
            response = await model.ainvoke([HumanMessage(content=prompt)])
            
            # 解析提取结果
            knowledge_text = response.content
            
            return {
                "learning_id": learning.learning_id,
                "knowledge_text": knowledge_text,
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "learning_id": learning.learning_id,
                "error": str(e),
                "created_at": datetime.now().isoformat()
            }
    
    async def create_best_practice(
        self,
        learning: Learning,
        db: Session
    ) -> BestPractice:
        """
        创建最佳实践
        
        Args:
            learning: 学习记录
            db: 数据库会话
            
        Returns:
            创建的最佳实践
        """
        try:
            # 提取知识
            knowledge_result = await self.extract_knowledge(learning, db)
            
            if "error" in knowledge_result:
                raise Exception(f"知识提取失败: {knowledge_result['error']}")
            
            # 解析知识文本（简化版本）
            knowledge_lines = knowledge_result["knowledge_text"].split('\n')
            title = knowledge_lines[0] if knowledge_lines else learning.summary
            description = knowledge_text = '\n'.join(knowledge_lines[1:]) if len(knowledge_lines) > 1 else learning.details
            
            # 生成最佳实践ID
            import random
            import string
            date_str = datetime.now().strftime("%Y%m%d")
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
            practice_id = f"BP-{date_str}-{random_str}"
            
            # 创建最佳实践
            best_practice = BestPractice(
                practice_id=practice_id,
                title=title,
                description=description,
                category=learning.area.value if learning.area else "general",
                priority=learning.priority,
                code_example=None,  # 可以从 knowledge_text 中提取
                source_learning_id=learning.learning_id
            )
            
            db.add(best_practice)
            db.commit()
            db.refresh(best_practice)
            
            return best_practice
        except Exception as e:
            db.rollback()
            raise Exception(f"创建最佳实践失败: {str(e)}")
    
    async def create_system_prompt(
        self,
        learning: Learning,
        db: Session
    ) -> SystemPrompt:
        """
        创建系统提示
        
        Args:
            learning: 学习记录
            db: 数据库会话
            
        Returns:
            创建的系统提示
        """
        try:
            # 构建提示生成
            prompt_key = f"auto_{learning.category.value}_{datetime.now().strftime('%Y%m%d')}"
            
            # 生成提示内容
            prompt_content = f"""# {learning.summary}

## 说明
{learning.details}

## 建议操作
{learning.suggested_action}

## 注意事项
在相关工作中应该遵循这个原则，避免类似问题再次发生。
"""
            
            # 创建系统提示
            system_prompt = SystemPrompt(
                prompt_key=prompt_key,
                prompt_type="behavior",
                content=prompt_content,
                priority=1,
                area=learning.area,
                tags=["auto-generated", "from-learning", learning.category.value]
            )
            
            db.add(system_prompt)
            db.commit()
            db.refresh(system_prompt)
            
            return system_prompt
        except Exception as e:
            db.rollback()
            raise Exception(f"创建系统提示失败: {str(e)}")


class KnowledgeTransformer:
    """知识转化器（整合所有转化功能）"""
    
    def __init__(self):
        self.summarizer = ExperienceSummarizer()
        self.extractor = KnowledgeExtractor()
    
    async def transform_learning(
        self,
        learning_id: str,
        target_type: str,  # best_practice, system_prompt
        db: Session
    ) -> Dict:
        """
        转化学习记录为知识
        
        Args:
            learning_id: 学习ID
            target_type: 目标类型
            db: 数据库会话
            
        Returns:
            转化结果
        """
        # 获取学习记录
        learning = db.query(Learning).filter(
            Learning.learning_id == learning_id
        ).first()
        
        if not learning:
            raise ValueError(f"学习记录 {learning_id} 不存在")
        
        # 根据目标类型转化
        if target_type == "best_practice":
            try:
                best_practice = await self.extractor.create_best_practice(learning, db)
                
                # 更新学习记录状态
                learning.status = "promoted"
                db.commit()
                
                return {
                    "success": True,
                    "type": "best_practice",
                    "id": best_practice.practice_id,
                    "title": best_practice.title
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        elif target_type == "system_prompt":
            try:
                system_prompt = await self.extractor.create_system_prompt(learning, db)
                
                # 更新学习记录状态
                learning.status = "promoted"
                learning.promoted_to = "system_prompts"
                db.commit()
                
                return {
                    "success": True,
                    "type": "system_prompt",
                    "id": system_prompt.prompt_key,
                    "content": system_prompt.content[:100] + "..."
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        else:
            return {
                "success": False,
                "error": f"不支持的目标类型: {target_type}"
            }
    
    async def promote_automatically(
        self,
        db: Session,
        min_recurrence: int = 3
    ) -> List[Dict]:
        """
        自动提升重复出现的学习记录
        
        Args:
            db: 数据库会话
            min_recurrence: 最小重复次数
            
        Returns:
            提升结果列表
        """
        # 获取重复次数高的学习记录
        learnings = db.query(Learning).filter(
            Learning.recurrence_count >= min_recurrence,
            Learning.status == "pending"
        ).all()
        
        results = []
        
        for learning in learnings:
            # 决定提升目标
            if learning.category.value in ["best_practice", "correction"]:
                target_type = "best_practice"
            else:
                target_type = "system_prompt"
            
            # 转化学习记录
            result = await self.transform_learning(
                learning.learning_id,
                target_type,
                db
            )
            
            results.append({
                "learning_id": learning.learning_id,
                "result": result
            })
        
        return results


# 全局单例
_knowledge_transformer_instance = None


def get_knowledge_transformer() -> KnowledgeTransformer:
    """获取全局知识转化器实例"""
    global _knowledge_transformer_instance
    if _knowledge_transformer_instance is None:
        _knowledge_transformer_instance = KnowledgeTransformer()
    return _knowledge_transformer_instance