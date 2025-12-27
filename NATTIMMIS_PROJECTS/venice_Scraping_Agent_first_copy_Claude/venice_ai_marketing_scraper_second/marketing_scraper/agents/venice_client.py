"""
Venice AI Client Wrapper - OpenAI Compatible
Handles all AI inference for the 5-agent marketing scraper system
"""

import os
import json
from typing import List, Dict, Any, Optional, Generator
from openai import OpenAI
from dataclasses import dataclass

@dataclass
class AgentConfig:
    """Configuration for each Venice AI agent"""
    name: str
    model: str
    system_prompt: str
    temperature: float = 0.7
    max_tokens: int = 4096

class VeniceClient:
    """
    Venice AI Client - Privacy-first AI inference
    Uses OpenAI-compatible API with Venice's uncensored models
    """
    
    MODELS = {
        "reasoning": "zai-org-glm-4.6",      # Deep reasoning, 128k context
        "uncensored": "venice-uncensored",    # Unfiltered generation
        "fast": "llama-3.3-70b",              # Fast inference
        "tool_calling": "qwen3-235b",         # Best for function calling
        "balanced": "mistral-31-24b"          # Good balance
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("VENICE_API_KEY", "")
        if not self.api_key:
            print("⚠️  VENICE_API_KEY not set - using demo mode")
            self.demo_mode = True
        else:
            self.demo_mode = False
            
        self.client = OpenAI(
            api_key=self.api_key if self.api_key else "demo-key",
            base_url="https://api.venice.ai/api/v1"
        )
        
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama-3.3-70b",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
        tools: Optional[List[Dict]] = None,
        enable_web_search: bool = False
    ) -> Dict[str, Any]:
        """
        Send chat completion request to Venice AI
        """
        if self.demo_mode:
            return self._demo_response(messages)
            
        try:
            params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream
            }
            
            # Add web search capability
            if enable_web_search:
                params["model"] = f"{model}:enable_web_search=auto"
                
            if tools:
                params["tools"] = tools
                
            response = self.client.chat.completions.create(**params)
            
            if stream:
                return self._handle_stream(response)
            
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            }
            
        except Exception as e:
            return {"error": str(e), "content": None}
    
    def _handle_stream(self, response) -> Generator[str, None, None]:
        """Handle streaming responses"""
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    def _demo_response(self, messages: List[Dict]) -> Dict[str, Any]:
        """Demo mode response when no API key is set"""
        last_msg = messages[-1]["content"] if messages else ""
        return {
            "content": f"[DEMO MODE] Venice AI would process: '{last_msg[:100]}...'",
            "model": "demo",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0}
        }
    
    def with_web_search(
        self,
        query: str,
        model: str = "llama-3.3-70b"
    ) -> Dict[str, Any]:
        """
        Query with web search enabled - scrapes real-time data
        """
        return self.chat(
            messages=[{"role": "user", "content": query}],
            model=model,
            enable_web_search=True
        )


class AgentBase:
    """Base class for all Venice AI agents"""
    
    def __init__(self, client: VeniceClient, config: AgentConfig):
        self.client = client
        self.config = config
        self.conversation_history: List[Dict[str, str]] = []
        
    def reset(self):
        """Reset conversation history"""
        self.conversation_history = []
        
    def think(self, user_input: str, context: Optional[Dict] = None) -> str:
        """
        Agent reasoning with context
        """
        messages = [
            {"role": "system", "content": self.config.system_prompt}
        ]
        
        # Add context if provided
        if context:
            context_str = json.dumps(context, indent=2)
            messages.append({
                "role": "system",
                "content": f"Current context:\n{context_str}"
            })
            
        # Add conversation history
        messages.extend(self.conversation_history)
        
        # Add current input
        messages.append({"role": "user", "content": user_input})
        
        response = self.client.chat(
            messages=messages,
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        if response.get("content"):
            # Update history
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": response["content"]})
            
        return response.get("content", response.get("error", "No response"))
