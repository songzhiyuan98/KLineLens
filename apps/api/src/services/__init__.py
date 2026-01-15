"""
KLineLens Services

服务模块，包含 LLM 叙事生成等功能。
"""

from .llm_service import LLMService, generate_narrative

__all__ = ["LLMService", "generate_narrative"]
