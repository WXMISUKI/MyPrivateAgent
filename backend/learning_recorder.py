"""
学习记录管理模块
"""
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from models import (
    Learning, LearningCategory, LearningStatus, Priority, Area,
    Error, FeatureRequest
)
from smart_detector import get_smart_detector, ErrorDetection, LearningOpportunity


class LearningRecorder:
    """学习记录器"""
    
    def __init__(self):
        self.detector = get_smart_detector()
    
    def record_from_conversation(
        self,
        conversation_text: str,
        db: Session,
        user_id: Optional[int] = None,
        area: Optional[Area] = None
    ) -> List[Dict]:
        """
        从对话中自动记录学习内容
        
        Args:
            conversation_text: 对话文本
            db: 数据库会话
            user_id: 用户ID
            area: 区域
            
        Returns:
            创建的学习记录列表
        """
        # 分析对话
        analysis = self.detector.analyze_conversation(conversation_text)
        
        # 判断是否应该记录
        if not self.detector.should_log_learning(analysis):
            return []
        
        created_records = []
        
        # 建议学习类型
        learning_type = self.detector.suggest_learning_type(analysis)
        
        # 如果有错误，记录为学习或错误
        if analysis["errors"]:
            for error in analysis["errors"]:
                if error["confidence"] >= 0.8:  # 只记录高置信度的错误
                    # 判断是学习还是错误记录
                    if error["type"] == "user_correction":
                        # 用户纠正，记录为学习
                        learning = self._create_learning_from_error(
                            error, learning_type, area, conversation_text
                        )
                        db.add(learning)
                        db.commit()
                        db.refresh(learning)
                        
                        created_records.append({
                            "type": "learning",
                            "id": learning.learning_id,
                            "summary": learning.summary
                        })
                    else:
                        # 系统错误，记录为错误
                        error_record = self._create_error_record(
                            error, area, conversation_text
                        )
                        db.add(error_record)
                        db.commit()
                        db.refresh(error_record)
                        
                        created_records.append({
                            "type": "error",
                            "id": error_record.error_id,
                            "summary": error_record.summary
                        })
        
        # 如果有学习机会
        if analysis["opportunities"]:
            for opportunity in analysis["opportunities"]:
                if opportunity["confidence"] >= 0.7:  # 只记录高置信度的机会
                    learning = self._create_learning_from_opportunity(
                        opportunity, area, conversation_text
                    )
                    db.add(learning)
                    db.commit()
                    db.refresh(learning)
                    
                    created_records.append({
                        "type": "learning",
                        "id": learning.learning_id,
                        "summary": learning.summary
                    })
        
        return created_records
    
    def _create_learning_from_error(
        self,
        error: Dict,
        learning_type: str,
        area: Optional[Area],
        context: str
    ) -> Learning:
        """从错误创建学习记录"""
        # 生成学习ID
        learning_id = self._generate_id("LRN")
        
        # 确定优先级
        priority = Priority.HIGH if error["confidence"] >= 0.9 else Priority.MEDIUM
        
        return Learning(
            learning_id=learning_id,
            category=LearningCategory[learning_type.upper()],
            priority=priority,
            status=LearningStatus.PENDING,
            area=area,
            summary=f"需要解决的错误: {error['pattern']}",
            details=f"检测到错误: {error['context']}",
            suggested_action=f"分析并解决 '{error['pattern']}' 相关问题",
            source="error",
            tags=["error", "auto-recorded"],
            first_seen=datetime.now(),
            last_seen=datetime.now()
        )
    
    def _create_error_record(
        self,
        error: Dict,
        area: Optional[Area],
        context: str
    ) -> Error:
        """创建错误记录"""
        import random
        import string
        
        # 生成错误ID
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
        error_id = f"ERR-{date_str}-{random_str}"
        
        return Error(
            error_id=error_id,
            priority=Priority.HIGH if error["confidence"] >= 0.9 else Priority.MEDIUM,
            status="pending",
            area=area,
            summary=f"检测到错误: {error['pattern']}",
            error_message=error['context'],
            context=context[:500],  # 限制长度
            suggested_fix="需要进一步调查和修复",
            reproducible=False
        )
    
    def _create_learning_from_opportunity(
        self,
        opportunity: Dict,
        area: Optional[Area],
        context: str
    ) -> Learning:
        """从学习机会创建学习记录"""
        # 生成学习ID
        learning_id = self._generate_id("LRN")
        
        # 确定学习类型
        learning_type = "insight" if opportunity["type"] in ["investigation", "调试", "debugging"] else "best_practice"
        
        return Learning(
            learning_id=learning_id,
            category=LearningCategory[learning_type.upper()],
            priority=Priority.MEDIUM,
            status=LearningStatus.PENDING,
            area=area,
            summary=f"发现学习机会: {opportunity['type']}",
            details=f"学习机会上下文: {opportunity['context']}",
            suggested_action=f"考虑将此经验转化为最佳实践",
            source="conversation",
            tags=["opportunity", "auto-recorded"],
            first_seen=datetime.now(),
            last_seen=datetime.now()
        )
    
    def _generate_id(self, prefix: str) -> str:
        """生成唯一ID"""
        import random
        import string
        
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
        return f"{prefix}-{date_str}-{random_str}"


class LearningManager:
    """学习管理器"""
    
    def __init__(self):
        self.recorder = LearningRecorder()
    
    def get_learnings(
        self,
        db: Session,
        status: Optional[str] = None,
        area: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        获取学习记录
        
        Args:
            db: 数据库会话
            status: 状态过滤
            area: 区域过滤
            category: 分类过滤
            limit: 限制数量
            
        Returns:
            学习记录列表
        """
        query = db.query(Learning)
        
        if status:
            query = query.filter(Learning.status == status)
        if area:
            query = query.filter(Learning.area == area)
        if category:
            query = query.filter(Learning.category == category)
        
        learnings = query.limit(limit).all()
        
        return [
            {
                "id": learning.learning_id,
                "category": learning.category.value,
                "priority": learning.priority.value,
                "status": learning.status.value,
                "area": learning.area.value if learning.area else None,
                "summary": learning.summary,
                "details": learning.details,
                "suggested_action": learning.suggested_action,
                "created_at": learning.created_at.isoformat(),
                "resolved_at": learning.resolved_at.isoformat() if learning.resolved_at else None
            }
            for learning in learnings
        ]
    
    def get_learning(self, learning_id: str, db: Session) -> Optional[Dict]:
        """
        获取单个学习记录
        
        Args:
            learning_id: 学习ID
            db: 数据库会话
            
        Returns:
            学习记录
        """
        learning = db.query(Learning).filter(
            Learning.learning_id == learning_id
        ).first()
        
        if not learning:
            return None
        
        return {
            "id": learning.learning_id,
            "category": learning.category.value,
            "priority": learning.priority.value,
            "status": learning.status.value,
            "area": learning.area.value if learning.area else None,
            "summary": learning.summary,
            "details": learning.details,
            "suggested_action": learning.suggested_action,
            "source": learning.source,
            "related_files": learning.related_files,
            "tags": learning.tags,
            "pattern_key": learning.pattern_key,
            "recurrence_count": learning.recurrence_count,
            "created_at": learning.created_at.isoformat(),
            "updated_at": learning.updated_at.isoformat(),
            "resolved_at": learning.resolved_at.isoformat() if learning.resolved_at else None,
            "promoted_to": learning.promoted_to
        }
    
    def resolve_learning(
        self,
        learning_id: str,
        notes: Optional[str] = None,
        promote_to: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict:
        """
        标记学习记录为已解决
        
        Args:
            learning_id: 学习ID
            notes: 解决说明
            promote_to: 提升到的文件
            db: 数据库会话
            
        Returns:
            更新后的学习记录
        """
        learning = db.query(Learning).filter(
            Learning.learning_id == learning_id
        ).first()
        
        if not learning:
            raise ValueError(f"Learning {learning_id} not found")
        
        learning.status = LearningStatus.RESOLVED
        learning.resolved_at = datetime.now()
        
        if promote_to:
            learning.status = LearningStatus.PROMOTED
            learning.promoted_to = promote_to
        
        db.commit()
        db.refresh(learning)
        
        return {
            "id": learning.learning_id,
            "status": learning.status.value,
            "resolved_at": learning.resolved_at.isoformat(),
            "promoted_to": learning.promoted_to
        }
    
    def get_statistics(self, db: Session) -> Dict:
        """
        获取统计信息
        
        Args:
            db: 数据库会话
            
        Returns:
            统计信息
        """
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
        
        return {
            "learnings": {
                "total": total_learnings,
                "pending": pending_learnings,
                "resolved": resolved_learnings
            },
            "errors": {
                "total": total_errors,
                "pending": pending_errors
            },
            "features": {
                "total": total_features,
                "pending": pending_features
            }
        }


# 全局单例
_learning_manager_instance = None


def get_learning_manager() -> LearningManager:
    """获取全局学习管理器实例"""
    global _learning_manager_instance
    if _learning_manager_instance is None:
        _learning_manager_instance = LearningManager()
    return _learning_manager_instance