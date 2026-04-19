"""
自动复盘模块
用于定期分析学习记录并生成优化建议
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from models import (
    Learning, LearningStatus, LearningCategory, Priority,
    Error, FeatureRequest, SystemPrompt
)
from model_router import get_model_router
from langchain_core.messages import HumanMessage, AIMessage
from knowledge_transformer import get_knowledge_transformer


class DailyReviewer:
    """每日复盘器"""
    
    def __init__(self):
        self.model_router = get_model_router()
        self.knowledge_transformer = get_knowledge_transformer()
    
    async def review_pending_learnings(
        self,
        db: Session,
        limit: int = 20
    ) -> Dict:
        """
        审查待处理的学习记录
        
        Args:
            db: 数据库会话
            limit: 限制数量
            
        Returns:
            审查结果
        """
        # 获取待处理的学习记录
        pending_learnings = db.query(Learning).filter(
            Learning.status == LearningStatus.PENDING
        ).order_by(Learning.created_at.desc()).limit(limit).all()
        
        results = []
        
        for learning in pending_learnings:
            # 判断是否需要提升
            should_promote = self._should_promote_learning(learning)
            
            result = {
                "learning_id": learning.learning_id,
                "category": learning.category.value,
                "priority": learning.priority.value,
                "summary": learning.summary,
                "should_promote": should_promote,
                "suggested_action": learning.suggested_action,
                "created_at": learning.created_at.isoformat()
            }
            
            results.append(result)
        
        return {
            "total_pending": len(pending_learnings),
            "reviewed": len(results),
            "recommend_promotion": sum(1 for r in results if r["should_promote"]),
            "results": results
        }
    
    def _should_promote_learning(self, learning: Learning) -> bool:
        """
        判断是否应该提升学习记录
        
        Args:
            learning: 学习记录
            
        Returns:
            是否应该提升
        """
        # 高优先级的学习记录应该提升
        if learning.priority == Priority.HIGH or learning.priority == Priority.CRITICAL:
            return True
        
        # 重复出现的学习记录应该提升
        if learning.recurrence_count >= 3:
            return True
        
        # 最佳实践类型的学习记录应该提升
        if learning.category == LearningCategory.BEST_PRACTICE:
            return True
        
        # 纠正类型的学习记录应该提升
        if learning.category == LearningCategory.CORRECTION:
            return True
        
        return False
    
    async def generate_review_summary(
        self,
        db: Session
    ) -> Dict:
        """
        生成复盘总结
        
        Args:
            db: 数据库会话
            
        Returns:
            复盘总结
        """
        # 获取统计信息
        total_learnings = db.query(Learning).count()
        pending_learnings = db.query(Learning).filter(
            Learning.status == LearningStatus.PENDING
        ).count()
        resolved_learnings = db.query(Learning).filter(
            Learning.status == LearningStatus.RESOLVED
        ).count()
        
        total_errors = db.query(Error).count()
        pending_errors = db.query(Error).filter(Error.status == "pending").count()
        
        total_features = db.query(FeatureRequest).count()
        pending_features = db.query(FeatureRequest).filter(
            FeatureRequest.status == "pending"
        ).count()
        
        # 获取最近的学习记录
        recent_learnings = db.query(Learning).order_by(
            Learning.created_at.desc()
        ).limit(5).all()
        
        # 生成总结文本
        prompt = f"""请生成每日复盘总结，分析以下数据：

统计数据：
- 学习记录总数: {total_learnings}
- 待处理学习记录: {pending_learnings}
- 已解决学习记录: {resolved_learnings}
- 错误总数: {total_errors}
- 待处理错误: {pending_errors}
- 功能请求总数: {total_features}
- 待处理功能请求: {pending_features}

最近学习记录（最多5条）:
{chr(10).join([f"{l.learning_id}: {l.summary}" for l in recent_learnings])}

请生成一份简洁的复盘总结，包括：
1. 总体状况评估
2. 需要优先处理的问题
3. 改进建议
4. 后续行动计划
"""
        
        try:
            try:
                model = self.model_router.get_model("doubao")
            except ValueError:
                # 豆包模型未配置，降级使用本地模型
                try:
                    model = self.model_router.get_model("llama3.1")
                except ValueError:
                    model = self.model_router.get_model("deepseek-r1:7b")
            
            response = await model.ainvoke([HumanMessage(content=prompt)])
            
            return {
                "summary": response.content,
                "stats": {
                    "total_learnings": total_learnings,
                    "pending_learnings": pending_learnings,
                    "resolved_learnings": resolved_learnings,
                    "total_errors": total_errors,
                    "pending_errors": pending_errors,
                    "total_features": total_features,
                    "pending_features": pending_features
                },
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "generated_at": datetime.now().isoformat(),
                "stats": {
                    "total_learnings": total_learnings,
                    "pending_learnings": pending_learnings,
                    "resolved_learnings": resolved_learnings,
                    "total_errors": total_errors,
                    "pending_errors": pending_errors,
                    "total_features": total_features,
                    "pending_features": pending_features
                }
            }
    
    async def auto_promote_learnings(
        self,
        db: Session,
        min_recurrence: int = 3
    ) -> Dict:
        """
        自动提升学习记录
        
        Args:
            db: 数据库会话
            min_recurrence: 最小重复次数
            
        Returns:
            提升结果
        """
        try:
            # 使用知识转化器自动提升
            results = await self.knowledge_transformer.promote_automatically(
                db, min_recurrence
            )
            
            successful = sum(1 for r in results if r["result"].get("success"))
            failed = sum(1 for r in results if not r["result"].get("success"))
            
            return {
                "total": len(results),
                "successful": successful,
                "failed": failed,
                "results": results,
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    def get_learning_trends(
        self,
        db: Session,
        days: int = 7
    ) -> Dict:
        """
        获取学习趋势
        
        Args:
            db: 数据库会话
            days: 统计天数
            
        Returns:
            趋势数据
        """
        # 获取指定天数的学习记录
        since_date = datetime.now() - timedelta(days=days)
        
        daily_stats = db.query(
            func.date(Learning.created_at).label('date'),
            Learning.category.label('category'),
            func.count(Learning.id).label('count')
        ).filter(
            Learning.created_at >= since_date
        ).group_by(
            func.date(Learning.created_at),
            Learning.category
        ).all()
        
        # 转换为字典格式
        trends = {}
        for stat in daily_stats:
            date_str = stat.date.strftime('%Y-%m-%d') if hasattr(stat.date, 'strftime') else str(stat.date)
            category = stat.category
            
            if date_str not in trends:
                trends[date_str] = {}
            
            trends[date_str][category] = stat.count
        
        return {
            "days": days,
            "start_date": since_date.isoformat(),
            "end_date": datetime.now().isoformat(),
            "trends": trends
        }
    
    def get_error_patterns(
        self,
        db: Session
    ) -> List[Dict]:
        """
        获取错误模式
        
        Args:
            db: 数据库会话
            
        Returns:
            错误模式列表
        """
        # 按优先级排序错误
        errors = db.query(Error).filter(
            Error.status == "pending"
        ).order_by(Error.priority.desc()).limit(20).all()
        
        patterns = []
        
        for error in errors:
            patterns.append({
                "error_id": error.error_id,
                "priority": error.priority.value,
                "summary": error.summary,
                "reproducible": error.reproducible,
                "related_files": error.related_files,
                "suggested_fix": error.suggested_fix,
                "created_at": error.created_at.isoformat()
            })
        
        return patterns


class OptimizationSuggester:
    """优化建议生成器"""
    
    def __init__(self):
        self.model_router = get_model_router()
    
    async def generate_optimization_suggestions(
        self,
        db: Session,
        limit: int = 5
    ) -> Dict:
        """
        生成优化建议
        
        Args:
            db: 数据库会话
            limit: 限制数量
            
        Returns:
            优化建议
        """
        # 获取高优先级的待处理问题
        high_priority_errors = db.query(Error).filter(
            and_(
                Error.status == "pending",
                Error.priority.in_([Priority.HIGH, Priority.CRITICAL])
            )
        ).limit(limit).all()
        
        high_priority_learnings = db.query(Learning).filter(
            and_(
                Learning.status == LearningStatus.PENDING,
                Learning.priority.in_([Priority.HIGH, Priority.CRITICAL])
            )
        ).limit(limit).all()
        
        if not high_priority_errors and not high_priority_learnings:
            return {
                "message": "没有需要优化的高优先级问题",
                "suggestions": []
            }
        
        # 构建分析数据
        analysis_data = []
        
        for error in high_priority_errors:
            analysis_data.append(f"错误: {error.summary} - {error.suggested_fix}")
        
        for learning in high_priority_learnings:
            analysis_data.append(f"学习: {learning.summary} - {learning.suggested_action}")
        
        # 生成优化建议
        prompt = f"""基于以下待处理问题，生成优化建议：

{chr(10).join(analysis_data)}

请提供以下格式的优化建议：
1. 问题分析：识别问题的根本原因
2. 优先级评估：评估每个问题的紧急程度
3. 建议行动：具体的解决步骤
4. 预期效果：优化后的预期效果
5. 资源需求：需要哪些资源
"""
        
        try:
            try:
                model = self.model_router.get_model("doubao")
            except ValueError:
                # 豆包模型未配置，降级使用本地模型
                try:
                    model = self.model_router.get_model("llama3.1")
                except ValueError:
                    model = self.model_router.get_model("deepseek-r1:7b")
            
            response = await model.ainvoke([HumanMessage(content=prompt)])
            
            return {
                "suggestions": [response.content],
                "total_issues": len(high_priority_errors) + len(high_priority_learnings),
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    async def suggest_improvement_priorities(
        self,
        db: Session
    ) -> Dict:
        """
        建议改进优先级
        
        Args:
            db: 数据库会话
            
        Returns:
            优先级建议
        """
        # 统计各类问题的数量
        critical_errors = db.query(Error).filter(
            and_(
                Error.status == "pending",
                Error.priority == Priority.CRITICAL
            )
        ).count()
        
        high_errors = db.query(Error).filter(
            and_(
                Error.status == "pending",
                Error.priority == Priority.HIGH
            )
        ).count()
        
        critical_learnings = db.query(Learning).filter(
            and_(
                Learning.status == LearningStatus.PENDING,
                Learning.priority == Priority.CRITICAL
            )
        ).count()
        
        high_learnings = db.query(Learning).filter(
            and_(
                Learning.status == LearningStatus.PENDING,
                Learning.priority == Priority.HIGH
            )
        ).count()
        
        pending_features = db.query(FeatureRequest).filter(
            FeatureRequest.status == "pending"
        ).count()
        
        # 生成优先级建议
        priority_order = []
        
        if critical_errors > 0:
            priority_order.append({
                "priority": "critical",
                "type": "error",
                "count": critical_errors,
                "suggestion": "立即处理关键错误，这些错误可能阻塞系统功能"
            })
        
        if critical_learnings > 0:
            priority_order.append({
                "priority": "critical",
                "type": "learning",
                "count": critical_learnings,
                "suggestion": "优先应用关键学习，这些知识对系统改进影响最大"
            })
        
        if high_errors > 0:
            priority_order.append({
                "priority": "high",
                "type": "error",
                "count": high_errors,
                "suggestion": "尽快处理高优先级错误，防止影响扩大"
            })
        
        if high_learnings > 0:
            priority_order.append({
                "priority": "high",
                "type": "learning",
                "count": high_learnings,
                "suggestion": "应用高优先级学习，提升系统性能和稳定性"
            })
        
        if pending_features > 0:
            priority_order.append({
                "priority": "medium",
                "type": "feature",
                "count": pending_features,
                "suggestion": "评估功能需求，决定是否实现"
            })
        
        return {
            "priorities": priority_order,
            "total_items": sum(p["count"] for p in priority_order),
            "generated_at": datetime.now().isoformat()
        }


class AutoReviewer:
    """自动复盘器（整合所有复盘功能）"""
    
    def __init__(self):
        self.daily_reviewer = DailyReviewer()
        self.optimization_suggester = OptimizationSuggester()
    
    async def run_daily_review(
        self,
        db: Session = Depends(None)
    ) -> Dict:
        """
        运行每日复盘
        
        Args:
            db: 数据库会话
            
        Returns:
            复盘结果
        """
        try:
            # 生成复盘总结
            summary = await self.daily_reviewer.generate_review_summary(db)
            
            # 获取学习趋势
            trends = self.daily_reviewer.get_learning_trends(db, days=7)
            
            # 获取错误模式
            error_patterns = self.daily_reviewer.get_error_patterns(db)
            
            # 获取优化建议
            suggestions = await self.optimization_suggester.generate_optimization_suggestions(db)
            
            # 获取优先级建议
            priorities = await self.optimization_suggester.suggest_improvement_priorities(db)
            
            return {
                "success": True,
                "summary": summary,
                "trends": trends,
                "error_patterns": error_patterns,
                "optimization_suggestions": suggestions,
                "priority_suggestions": priorities,
                "review_date": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "review_date": datetime.now().isoformat()
            }
    
    async def run_auto_promotion(
        self,
        db: Session = Depends(None)
    ) -> Dict:
        """
        运行自动提升
        
        Args:
            db: 数据库会话
            
        Returns:
            提升结果
        """
        return await self.daily_reviewer.auto_promote_learnings(db)


# 全局单例
_auto_reviewer_instance = None


def get_auto_reviewer() -> AutoReviewer:
    """获取全局自动复盘器实例"""
    global _auto_reviewer_instance
    if _auto_reviewer_instance is None:
        _auto_reviewer_instance = AutoReviewer()
    return _auto_reviewer_instance