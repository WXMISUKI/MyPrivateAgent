"""
智能检测模块
用于检测错误、学习机会和模式
"""
from typing import List, Optional, Dict
from datetime import datetime
import re
from collections import defaultdict


class ErrorDetection:
    """错误检测结果"""
    def __init__(self, type: str, pattern: str, confidence: float, context: str = ""):
        self.type = type
        self.pattern = pattern
        self.confidence = confidence
        self.context = context


class LearningOpportunity:
    """学习机会"""
    def __init__(self, type: str, confidence: float, message_id: Optional[int] = None, context: str = ""):
        self.type = type
        self.confidence = confidence
        self.message_id = message_id
        self.context = context


class ErrorDetector:
    """错误检测器"""
    
    def __init__(self):
        # 系统错误模式
        self.error_patterns = [
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
            "connection failed",
            "连接失败",
            "超时",
            "异常"
        ]
        
        # 用户纠正模式
        self.correction_patterns = [
            "no, that's not right",
            "actually, it should be",
            "you're wrong about",
            "that's outdated",
            "纠正",
            "错误",
            "不对",
            "应该"
        ]
    
    def detect_errors(self, text: str) -> List[ErrorDetection]:
        """
        检测文本中的错误
        
        Args:
            text: 要检测的文本
            
        Returns:
            错误检测结果列表
        """
        detections = []
        text_lower = text.lower()
        
        # 检测系统错误
        for pattern in self.error_patterns:
            if pattern.lower() in text_lower:
                # 计算置信度
                confidence = self._calculate_confidence(pattern, text)
                
                # 提取上下文
                context = self._extract_context(text, pattern)
                
                detections.append(ErrorDetection(
                    type="system_error",
                    pattern=pattern,
                    confidence=confidence,
                    context=context
                ))
        
        # 检测用户纠正
        for pattern in self.correction_patterns:
            if pattern.lower() in text_lower:
                confidence = self._calculate_confidence(pattern, text)
                context = self._extract_context(text, pattern)
                
                detections.append(ErrorDetection(
                    type="user_correction",
                    pattern=pattern,
                    confidence=confidence,
                    context=context
                ))
        
        return detections
    
    def _calculate_confidence(self, pattern: str, text: str) -> float:
        """计算置信度"""
        # 基础置信度
        base_confidence = 0.7
        
        # 如果模式在文本开头，置信度更高
        if pattern.lower() in text[:100].lower():
            base_confidence += 0.2
        
        # 如果模式多次出现，置信度更高
        count = text.lower().count(pattern.lower())
        if count > 1:
            base_confidence += min(0.1 * (count - 1), 0.2)
        
        # 限制最大置信度
        return min(base_confidence, 0.95)
    
    def _extract_context(self, text: str, pattern: str, context_length: int = 100) -> str:
        """提取上下文"""
        try:
            # 查找模式位置
            pattern_lower = pattern.lower()
            text_lower = text.lower()
            idx = text_lower.find(pattern_lower)
            
            if idx == -1:
                return ""
            
            # 提取上下文
            start = max(0, idx - context_length // 2)
            end = min(len(text), idx + len(pattern) + context_length // 2)
            
            return text[start:end]
        except:
            return ""


class OpportunityIdentifier:
    """机会识别器"""
    
    def __init__(self):
        # 学习机会模式
        self.opportunity_patterns = [
            # 发现非显而易见的解决方案
            {"pattern": "investigation", "weight": 0.8, "zh": "调查"},
            {"pattern": "调试", "weight": 0.9, "zh": "调试"},
            {"pattern": "debugging", "weight": 0.8, "zh": "调试"},
            
            # 发现更好的方法
            {"pattern": "improved", "weight": 0.7, "zh": "改进"},
            {"pattern": "优化", "weight": 0.8, "zh": "优化"},
            {"pattern": "optimize", "weight": 0.7, "zh": "优化"},
            
            # 学习项目特定模式
            {"pattern": "convention", "weight": 0.9, "zh": "约定"},
            {"pattern": "pattern", "weight": 0.7, "zh": "模式"},
            {"pattern": "注意", "weight": 0.9, "zh": "注意"},
            
            # 用户主动分享知识
            {"pattern": "note that", "weight": 0.8, "zh": "注意"},
            {"pattern": "remember", "weight": 0.7, "zh": "记住"},
            
            # 发现问题解决方案
            {"pattern": "fix", "weight": 0.7, "zh": "修复"},
            {"pattern": "solution", "weight": 0.8, "zh": "解决方案"},
            {"pattern": "解决", "weight": 0.8, "zh": "解决"},
            
            # 发现新的工具或方法
            {"pattern": "useful", "weight": 0.7, "zh": "有用"},
            {"pattern": "helpful", "weight": 0.7, "zh": "有帮助"},
            {"pattern": "发现", "weight": 0.8, "zh": "发现"},
        ]
    
    def identify_opportunities(self, text: str) -> List[LearningOpportunity]:
        """
        识别学习机会
        
        Args:
            text: 要分析的文本
            
        Returns:
            学习机会列表
        """
        opportunities = []
        text_lower = text.lower()
        
        for pattern_info in self.opportunity_patterns:
            pattern = pattern_info["pattern"]
            zh_pattern = pattern_info["zh"]
            weight = pattern_info["weight"]
            
            # 检查英文模式
            if pattern.lower() in text_lower:
                confidence = weight
                context = self._extract_context(text, pattern)
                
                opportunities.append(LearningOpportunity(
                    type=pattern,
                    confidence=confidence,
                    context=context
                ))
            
            # 检查中文模式
            if zh_pattern and zh_pattern in text:
                confidence = weight
                context = self._extract_context(text, zh_pattern)
                
                opportunities.append(LearningOpportunity(
                    type=zh_pattern,
                    confidence=confidence,
                    context=context
                ))
        
        return opportunities
    
    def _extract_context(self, text: str, pattern: str, context_length: int = 100) -> str:
        """提取上下文"""
        try:
            # 查找模式位置
            idx = text.find(pattern)
            
            if idx == -1:
                return ""
            
            # 提取上下文
            start = max(0, idx - context_length // 2)
            end = min(len(text), idx + len(pattern) + context_length // 2)
            
            return text[start:end]
        except:
            return ""


class PatternDetector:
    """模式检测器"""
    
    def __init__(self):
        self.pattern_tracker = defaultdict(lambda: {
            "count": 0,
            "first_seen": None,
            "last_seen": None,
            "patterns": []
        })
    
    def detect_recurring_patterns(self, pattern_key: str, detection) -> bool:
        """
        检测重复模式
        
        Args:
            pattern_key: 模式键值
            detection: 错误检测结果
            
        Returns:
            是否为重复模式
        """
        # 支持传入 ErrorDetection 对象或 dict
        if isinstance(detection, dict):
            pattern_value = detection.get("pattern", "")
        else:
            pattern_value = detection.pattern
        
        tracker = self.pattern_tracker[pattern_key]
        
        # 如果这是第一次看到这个模式
        if tracker["count"] == 0:
            tracker["count"] = 1
            tracker["first_seen"] = datetime.now()
            tracker["last_seen"] = datetime.now()
            tracker["patterns"].append(pattern_value)
            return False
        
        # 增加计数
        tracker["count"] += 1
        tracker["last_seen"] = datetime.now()
        
        # 避免重复添加相同的模式
        if pattern_value not in tracker["patterns"]:
            tracker["patterns"].append(pattern_value)
        
        return True
    
    def get_pattern_stats(self, pattern_key: str) -> Dict:
        """
        获取模式统计信息
        
        Args:
            pattern_key: 模式键值
            
        Returns:
            模式统计信息
        """
        tracker = self.pattern_tracker[pattern_key]
        
        return {
            "pattern_key": pattern_key,
            "count": tracker["count"],
            "first_seen": tracker["first_seen"],
            "last_seen": tracker["last_seen"],
            "patterns": tracker["patterns"],
            "is_recurring": tracker["count"] >= 3
        }
    
    def get_all_recurring_patterns(self, min_count: int = 3) -> List[Dict]:
        """
        获取所有重复模式
        
        Args:
            min_count: 最小重复次数
            
        Returns:
            重复模式列表
        """
        recurring = []
        
        for pattern_key, tracker in self.pattern_tracker.items():
            if tracker["count"] >= min_count:
                recurring.append(self.get_pattern_stats(pattern_key))
        
        # 按计数排序
        recurring.sort(key=lambda x: x["count"], reverse=True)
        
        return recurring
    
    def generate_pattern_key(self, detection: ErrorDetection) -> str:
        """
        生成模式键值
        
        Args:
            detection: 错误检测结果
            
        Returns:
            模式键值
        """
        # 支持传入 ErrorDetection 对象或 dict
        if isinstance(detection, dict):
            error_type = detection.get("type", "unknown")
            pattern = detection.get("pattern", "unknown")
        else:
            error_type = detection.type
            pattern = detection.pattern
        
        # 基于类型和模式生成键值
        base_key = f"{error_type}_{pattern}"
        
        # 清理键值（移除特殊字符）
        base_key = re.sub(r'[^\w]', '_', base_key)
        
        # 转为小写
        return base_key.lower()


class SmartDetector:
    """智能检测器（整合所有检测功能）"""
    
    def __init__(self):
        self.error_detector = ErrorDetector()
        self.opportunity_identifier = OpportunityIdentifier()
        self.pattern_detector = PatternDetector()
    
    def analyze_conversation(self, text: str) -> Dict:
        """
        分析对话文本
        
        Args:
            text: 对话文本
            
        Returns:
            分析结果
        """
        # 检测错误
        errors = self.error_detector.detect_errors(text)
        
        # 识别学习机会
        opportunities = self.opportunity_identifier.identify_opportunities(text)
        
        # 检测重复模式
        recurring_patterns = []
        for error in errors:
            pattern_key = self.pattern_detector.generate_pattern_key(error)
            if self.pattern_detector.detect_recurring_patterns(pattern_key, error):
                pattern_stats = self.pattern_detector.get_pattern_stats(pattern_key)
                recurring_patterns.append(pattern_stats)
        
        return {
            "errors": [
                {
                    "type": error.type,
                    "pattern": error.pattern,
                    "confidence": error.confidence,
                    "context": error.context
                }
                for error in errors
            ],
            "opportunities": [
                {
                    "type": opp.type,
                    "confidence": opp.confidence,
                    "context": opp.context
                }
                for opp in opportunities
            ],
            "recurring_patterns": recurring_patterns
        }
    
    def should_log_learning(self, analysis: Dict) -> bool:
        """
        判断是否应该记录学习
        
        Args:
            analysis: 分析结果
            
        Returns:
            是否应该记录
        """
        # 如果有高置信度的错误
        high_conf_errors = [
            e for e in analysis["errors"]
            if e["confidence"] >= 0.8
        ]
        if high_conf_errors:
            return True
        
        # 如果有学习机会
        if analysis["opportunities"]:
            return True
        
        # 如果有重复模式
        if analysis["recurring_patterns"]:
            return True
        
        return False
    
    def suggest_learning_type(self, analysis: Dict) -> str:
        """
        建议学习类型
        
        Args:
            analysis: 分析结果
            
        Returns:
            学习类型
        """
        # 检查是否有用户纠正
        user_corrections = [
            e for e in analysis["errors"]
            if e["type"] == "user_correction"
        ]
        if user_corrections:
            return "correction"
        
        # 检查是否有系统错误
        system_errors = [
            e for e in analysis["errors"]
            if e["type"] == "system_error"
        ]
        if system_errors:
            return "knowledge_gap"
        
        # 检查是否有学习机会
        if analysis["opportunities"]:
            return "insight"
        
        # 默认返回
        return "best_practice"


# 全局单例
_smart_detector_instance = None


def get_smart_detector() -> SmartDetector:
    """获取全局智能检测器实例"""
    global _smart_detector_instance
    if _smart_detector_instance is None:
        _smart_detector_instance = SmartDetector()
    return _smart_detector_instance