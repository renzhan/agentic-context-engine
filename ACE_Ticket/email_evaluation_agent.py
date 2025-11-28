# -*- coding: utf-8 -*-
"""
EmailEvaluationAgent - 邮件回复质量评估Agent

负责评估ACE生成的邮件回复质量，重点关注是否包含具体的工作流程
"""

import json
import logging
from typing import Dict, Optional
from ace import EnvironmentResult


class EmailEvaluationAgent:
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

# 评估重点（按重要性排序）
**最重要：工作流程内容相似度 (70%)**
- 比对真实回复(ground_truth)和AI回复中的**具体工作步骤**
- 重点检查以下实体是否一致：
  * 人名（如Frances Parro Belleza、Cody Gorsuch、Michael Jan Francisco）
  * 系统名（如WMS、EDI、API）
  * 团队名（如Joliet团队、B-Solutions、Unis）
  * 配置值/关键字段（如'Regular Order'、订单类型）
  * 具体操作（如"协调讨论"、"检查"、"确认"、"整合反馈"）

评分规则：
- 1.0分：所有关键实体都出现，步骤顺序合理
- 0.8分：80%以上的关键实体出现
- 0.6分：60%以上的关键实体出现，但缺少重要步骤
- <0.6分：缺少大量关键实体或步骤逻辑错误

**次要：其他维度 (30%)**
- 准确性 (15%)：是否正确理解了邮件意图？
- 完整性 (10%)：是否涵盖了所有要点？
- 语气一致性 (5%)：语气是否与真人回复接近？

# 评分标准
- score >= 0.85: 优秀，包含了ground_truth中的几乎所有关键实体和步骤
- 0.7 <= score < 0.85: 良好，包含了大部分关键实体，但有遗漏
- 0.5 <= score < 0.7: 及格，包含了部分关键实体，缺少重要内容
- score < 0.5: 较差，缺少大量关键实体或理解有误

# 输出格式
必须返回有效的JSON，格式如下：
{
    "score": 0.85,
    "workflow_similarity": 0.9,
    "key_entities_matched": ["Frances Parro Belleza", "WMS", "Regular Order"],
    "key_entities_missing": ["Joliet团队"],
    "accuracy": 0.9,
    "completeness": 0.8,
    "tone_match": 0.85,
    "feedback": "具体的改进建议（特别指出缺少了哪些关键实体或步骤）",
    "workflow_steps_matched": 5,
    "workflow_steps_total": 6,
    "reasoning": "详细说明为什么给这个分数，特别是哪些关键实体匹配了，哪些缺失了"
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
# 原始邮件
{email_context.get('original_email', '')}

# 邮件历史（上下文）
{email_context.get('history', '无历史记录')}

# 用户真实回复（参考标准）
{ground_truth_reply}

# AI生成的回复
{generated_reply}

# 任务
1. **首先从真实回复中提取关键实体**：
   - 人名、系统名、团队名、配置值等
   - 具体的操作步骤和顺序
   
2. **然后检查AI回复中是否包含这些关键实体**：
   - 逐一比对人名（如Frances Parro Belleza、Cody Gorsuch等）
   - 逐一比对系统/配置（如WMS、EDI、'Regular Order'等）
   - 逐一比对团队/组织（如Joliet团队、B-Solutions等）
   
3. **计算相似度**：
   - 匹配了多少关键实体？
   - 匹配了多少工作步骤？
   - 步骤顺序是否合理？
   
4. **给出评分**：
   - 工作流程相似度占70%权重（关键实体和步骤匹配度）
   - 其他维度占30%权重

请按照系统提示中的JSON格式输出，特别要列出key_entities_matched和key_entities_missing。
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
        """格式化反馈信息（强调关键实体匹配情况）"""
        feedback_parts = [eval_data.get('feedback', '')]
        
        # 添加关键实体匹配信息
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

