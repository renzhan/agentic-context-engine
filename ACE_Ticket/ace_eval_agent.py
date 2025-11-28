# -*- coding: utf-8 -*-
"""
ACEEvaluationAgent - 邮件回复质量评估Agent

负责评估ACE生成的邮件回复质量，重点关注是否包含具体的工作流程
"""

import json
import logging
from typing import Dict, Optional
from ace import EnvironmentResult


class ACEEvaluationAgent:
    """
    邮件回复质量评估Agent
    
    核心职责：
    1. 调用LLM评估生成的回复是否和真人回复一致
    2. 重点关注：是否包含具体的工作流程/步骤
    3. 返回评分和改进建议
    """
    
    def __init__(self, llm_client):
        """
        Args:
            llm_client: LLM客户端（LiteLLMClient）
        """
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """加载评估系统prompt"""
        return """你是一个专业的邮件回复质量评估专家。

**⚠️ 重要格式要求：必须返回纯JSON，不要使用 ```json``` markdown标记！直接输出JSON对象！**

你的核心任务是评估AI生成的邮件回复，与用户真实回复对比，判断质量。

# 评估流程（必须严格按照以下步骤执行）

## 步骤1：提取真实回复的要点
首先，从真实回复(ground_truth)中提取所有要点，包括：
- **关键实体**：人名、系统名、团队名、配置值等
- **工作步骤**：具体的操作步骤和顺序
- **核心信息**：重要的事实、数据、时间等
- **意图/目的**：回复的主要目的和要解决的问题

将要点组织成结构化列表，每个要点包含：
- 要点类型（实体/步骤/信息/意图）
- 具体内容
- 重要性（高/中/低）

## 步骤2：提取生成回复的要点
然后，从AI生成的回复中提取所有要点，使用相同的结构：
- **关键实体**：识别出的人名、系统名、团队名、配置值等
- **工作步骤**：识别出的操作步骤
- **核心信息**：识别出的事实、数据、时间等
- **意图/目的**：识别出的回复目的

## 步骤3：要点匹配和评分
对每个真实回复的要点，在生成回复中查找匹配项：
- **完全匹配**：生成回复中包含相同的关键实体和步骤（1.0分）
- **部分匹配**：生成回复中包含部分关键信息，但缺少细节（0.6-0.8分）
- **不匹配**：生成回复中完全缺少该要点（0分）

## 步骤4：计算综合得分
- **工作流程相似度 (70%权重)**：基于要点匹配度，特别是关键实体和工作步骤
- **准确性 (15%权重)**：是否正确理解了邮件意图
- **完整性 (10%权重)**：是否涵盖了所有重要要点
- **语气一致性 (5%权重)**：语气是否与真人回复接近

# 评分规则
- 1.0分：所有关键要点都完全匹配，步骤顺序合理
- 0.8-0.9分：80%以上的关键要点匹配，少量次要要点缺失
- 0.6-0.7分：60%以上的关键要点匹配，但缺少重要步骤或关键实体
- 0.4-0.5分：只有部分要点匹配，缺少大量关键信息
- <0.4分：要点匹配度很低，理解有误

# 输出格式
必须返回有效的JSON，格式如下：
{
    "score": 0.85,
    "ground_truth_points": [
        {
            "type": "关键实体",
            "content": "Frances Parro Belleza",
            "importance": "高"
        },
        {
            "type": "工作步骤",
            "content": "第一步：联系Joliet团队协调讨论",
            "importance": "高"
        }
    ],
    "generated_points": [
        {
            "type": "关键实体",
            "content": "Frances Parro Belleza",
            "importance": "高"
        }
    ],
    "point_matches": [
        {
            "ground_truth_index": 0,
            "generated_index": 0,
            "match_score": 1.0,
            "match_type": "完全匹配"
        },
        {
            "ground_truth_index": 1,
            "generated_index": null,
            "match_score": 0.0,
            "match_type": "不匹配",
            "missing_content": "联系Joliet团队协调讨论"
        }
    ],
    "workflow_similarity": 0.9,
    "key_entities_matched": ["Frances Parro Belleza", "WMS"],
    "key_entities_missing": ["Joliet团队"],
    "accuracy": 0.9,
    "completeness": 0.8,
    "tone_match": 0.85,
    "feedback": "具体的改进建议（特别指出缺少了哪些要点）",
    "workflow_steps_matched": 5,
    "workflow_steps_total": 6,
    "reasoning": "详细说明要点提取和匹配过程，为什么给这个分数"
}
"""
    
    def evaluate_reply(
        self,
        generated_reply: str,
        ground_truth_reply: str,
        email_context: Dict
    ) -> EnvironmentResult:
        """
        评估生成的邮件回复
        
        Args:
            generated_reply: ACE生成的回复
            ground_truth_reply: 用户真实的回复
            email_context: 邮件上下文
        
        Returns:
            EnvironmentResult: ACE需要的评估结果
        """
        
        # 构造评估请求
        evaluation_request = self._build_evaluation_request(
            generated_reply=generated_reply,
            ground_truth_reply=ground_truth_reply,
            email_context=email_context
        )
        
        try:
            # 构造完整prompt
            full_prompt = f"{self.system_prompt}\n\n{evaluation_request}"
            
            # 调用LLM评估
            response = self.llm_client.complete(full_prompt)
            
            # 解析评估结果
            eval_data = self._parse_evaluation_response(response.text)
            
            self.logger.info(f"评估完成，得分: {eval_data['score']}")
            
            # 转换为ACE需要的格式
            return EnvironmentResult(
                feedback=self._format_feedback(eval_data),
                ground_truth=ground_truth_reply,
                metrics={
                    'score': eval_data['score'],  # 总分（0-1范围）
                    'workflow_similarity': eval_data.get('workflow_similarity', 0),  # 工作流程相似度（70%权重）
                    'entities_matched_count': len(eval_data.get('key_entities_matched', [])),  # 匹配的关键实体数量
                    'entities_missing_count': len(eval_data.get('key_entities_missing', [])),  # 缺失的关键实体数量
                    'workflow_steps_matched': eval_data.get('workflow_steps_matched', 0),  # 匹配的步骤数
                    'workflow_steps_total': eval_data.get('workflow_steps_total', 0),  # 总步骤数
                    'accuracy': eval_data.get('accuracy', 0),
                    'completeness': eval_data.get('completeness', 0),
                    'tone_match': eval_data.get('tone_match', 0)
                }
            )
        
        except Exception as e:
            self.logger.error(f"评估失败: {str(e)}")
            # 返回错误结果
            return EnvironmentResult(
                feedback=f"评估过程出错: {str(e)}",
                ground_truth=ground_truth_reply,
                metrics={'score': 0.3}
            )
    
    def _build_evaluation_request(self, generated_reply, ground_truth_reply, email_context):
        """构造评估请求"""
        return f"""
# 邮件上下文
## 原始邮件
{email_context.get('original_email', '')}

## 邮件历史（上下文）
{email_context.get('history', '无历史记录')}

---

# 评估任务

## 用户真实回复（参考标准）
{ground_truth_reply}

## AI生成的回复
{generated_reply}

---

# 请按照以下步骤进行评估：

## 步骤1：提取真实回复的要点
请仔细分析真实回复，提取所有要点，包括：
- **关键实体**：人名（如Frances Parro Belleza、Cody Gorsuch、Michael Jan Francisco）、系统名（如WMS、EDI、API）、团队名（如Joliet团队、B-Solutions）、配置值（如'Regular Order'）等
- **工作步骤**：具体的操作步骤，按顺序列出（如"第一步：联系Joliet团队协调讨论"、"第二步：检查WMS配置"等）
- **核心信息**：重要的事实、数据、时间、订单号等
- **意图/目的**：回复的主要目的和要解决的问题

为每个要点标注：
- 要点类型（关键实体/工作步骤/核心信息/意图）
- 具体内容
- 重要性（高/中/低）

## 步骤2：提取生成回复的要点
请仔细分析AI生成的回复，提取所有要点，使用相同的结构：
- **关键实体**：识别出的人名、系统名、团队名、配置值等
- **工作步骤**：识别出的操作步骤
- **核心信息**：识别出的事实、数据、时间等
- **意图/目的**：识别出的回复目的

## 步骤3：要点匹配
对每个真实回复的要点，在生成回复中查找匹配项：
- 检查是否包含相同的关键实体
- 检查是否包含相同的工作步骤
- 检查步骤顺序是否一致
- 检查核心信息是否一致
- 检查意图是否一致

为每个匹配项计算匹配分数：
- **完全匹配**（1.0分）：生成回复中包含相同的关键实体和步骤，内容一致
- **部分匹配**（0.6-0.8分）：生成回复中包含部分关键信息，但缺少细节或略有差异
- **不匹配**（0.0分）：生成回复中完全缺少该要点

## 步骤4：计算综合得分
基于要点匹配结果计算：
- **工作流程相似度 (70%权重)**：基于要点匹配度，特别是关键实体和工作步骤的匹配情况
- **准确性 (15%权重)**：是否正确理解了邮件意图
- **完整性 (10%权重)**：是否涵盖了所有重要要点
- **语气一致性 (5%权重)**：语气是否与真人回复接近

最终得分 = 工作流程相似度 × 0.7 + 准确性 × 0.15 + 完整性 × 0.1 + 语气一致性 × 0.05

---

**请严格按照系统提示中的JSON格式输出，必须包含：**
- ground_truth_points：真实回复的要点列表
- generated_points：生成回复的要点列表
- point_matches：要点匹配结果列表
- 其他评分指标

**重要：必须返回纯JSON，不要使用 ```json``` markdown标记！**
"""
    
    def _parse_evaluation_response(self, response: str) -> Dict:
        """解析LLM返回的评估结果"""
        try:
            # 尝试直接解析JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # 如果不是纯JSON，尝试提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # 解析失败，返回默认值
                self.logger.warning(f"无法解析评估结果，返回默认低分: {response[:100]}")
                return {
                    "score": 0.5,
                    "feedback": "评估结果格式错误",
                    "reasoning": "LLM返回格式不符合预期"
                }
    
    def _format_feedback(self, eval_data: Dict) -> str:
        """格式化反馈信息（强调要点匹配情况）"""
        feedback_parts = [eval_data.get('feedback', '')]
        
        # 添加要点匹配信息（如果存在）
        if eval_data.get('point_matches'):
            point_matches = eval_data['point_matches']
            matched_count = sum(1 for m in point_matches if m.get('match_score', 0) > 0.6)
            total_count = len(point_matches)
            avg_match_score = sum(m.get('match_score', 0) for m in point_matches) / total_count if total_count > 0 else 0
            feedback_parts.append(
                f"要点匹配: {matched_count}/{total_count} ({matched_count/total_count*100:.0f}%) 平均匹配度: {avg_match_score:.2f}"
            )
            
            # 显示不匹配的要点
            missing_points = [m for m in point_matches if m.get('match_score', 0) < 0.6]
            if missing_points:
                missing_contents = [m.get('missing_content', '') for m in missing_points[:3] if m.get('missing_content')]
                if missing_contents:
                    feedback_parts.append(
                        f"缺失要点: {', '.join(missing_contents)}"
                    )
        
        # 添加关键实体匹配信息（兼容旧格式）
        if eval_data.get('key_entities_matched'):
            matched = eval_data['key_entities_matched']
            feedback_parts.append(
                f"✓ 匹配的关键实体({len(matched)}个): {', '.join(matched[:5])}"  # 显示前5个
            )
        
        if eval_data.get('key_entities_missing'):
            missing = eval_data['key_entities_missing']
            feedback_parts.append(
                f"✗ 缺失的关键实体({len(missing)}个): {', '.join(missing[:5])}"
            )
        
        # 添加步骤匹配信息
        steps_matched = eval_data.get('workflow_steps_matched', 0)
        steps_total = eval_data.get('workflow_steps_total', 0)
        if steps_total > 0:
            feedback_parts.append(
                f"步骤匹配度: {steps_matched}/{steps_total} ({steps_matched/steps_total*100:.0f}%)"
            )
        
        return " | ".join(filter(None, feedback_parts))

