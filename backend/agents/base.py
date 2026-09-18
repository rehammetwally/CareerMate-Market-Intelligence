"""
Base Agent Class for DEPI Multi-Agent System
=============================================

Provides common functionality for all specialized agents.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentState(BaseModel):
    """Base state model for agent communication"""
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, llm, name: str = "BaseAgent"):
        self.llm = llm
        self.name = name
        self.logger = logging.getLogger(f"agents.{name}")
    
    _rotation_hooks = {} # Provider-specific rotation hooks
    
    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the current state and return updated state"""
        pass
    
    async def invoke_llm(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        image_data: Optional[str] = None,
        retries: int = 3
    ) -> str:
        """Invoke the LLM with the given prompt"""
        try:
            messages = []
            if system_message:
                from langchain_core.messages import SystemMessage, HumanMessage
                messages = [SystemMessage(content=system_message)]
                if image_data:
                    messages.append(HumanMessage(content=[
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]))
                else:
                    messages.append(HumanMessage(content=prompt))
            else:
                from langchain_core.messages import HumanMessage
                if image_data:
                    messages = [HumanMessage(content=[
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ])]
                else:
                    messages = [HumanMessage(content=prompt)]
            
            if hasattr(self.llm, 'ainvoke'):
                response = await self.llm.ainvoke(messages)
            else:
                import asyncio
                response = await asyncio.to_thread(self.llm.invoke, messages)
            
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            error_str = str(e).lower()
            is_rate_limit = "429" in error_str or "rate_limit" in error_str or "too many requests" in error_str
            
            if is_rate_limit and retries > 0:
                # Detect provider
                provider = None
                llm_type = str(type(self.llm)).lower()
                if "groq" in llm_type:
                    provider = "groq"
                elif "google" in llm_type:
                    provider = "gemini"
                
                if provider and provider in self._rotation_hooks:
                    self.log_info(f"Rate limit hit for {provider}. Attempting rotation...")
                    hook = self._rotation_hooks[provider]
                    try:
                        import asyncio
                        if asyncio.iscoroutinefunction(hook):
                            new_llm = await hook()
                        else:
                            new_llm = hook()
                        
                        if new_llm:
                            self.llm = new_llm
                            self.log_info(f"Rotation successful. Retrying {self.name} query...")
                            return await self.invoke_llm(prompt, system_message, image_data, retries - 1)
                    except Exception as rotation_err:
                        self.logger.error(f"Rotation hook failed: {rotation_err}")
                
            self.logger.error(f"{self.name} LL error: {e}")
            raise
    
    def log_info(self, message: str):
        self.logger.info(f"[{self.name}] {message}")
    
    def log_warning(self, message: str):
        self.logger.warning(f"[{self.name}] {message}")

    def log_error(self, message: str):
        self.logger.error(f"[{self.name}] {message}")
