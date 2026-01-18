#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Client - Multi-provider AI integration with fallback chain

Supports Claude Code (local auth), OpenAI CLI sessions, GPT-4 Turbo API keys,
OpenRouter "Mimo Flash" free tier, Ollama, and guided manual fallbacks.
Implements automatic fallback logic for robust ticket processing with
account-first detection.

Version: 1.0.0
"""

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import time

from .config import get_config
from .log_utils import log_event
from .state_paths import get_actifix_paths
from .security.rate_limiter import get_rate_limiter, RateLimitError


class AIProvider(Enum):
    """Supported AI providers."""
    CLAUDE_LOCAL = "claude_local"
    CLAUDE_API = "claude_api"
    OPENAI_CLI = "openai_cli"
    OPENAI = "openai"
    OLLAMA = "ollama"
    FREE_ALTERNATIVE = "free_alternative"


DEFAULT_FREE_MODEL = "mimo-flash-v2-free"
GROK4_FAST_MODEL = "openrouter/grok-4o-fast"
AI_PROVIDER_OPTIONS = [
    {
        "value": "auto",
        "label": "Auto (Do_AF fallback chain)",
        "description": "Try the best available provider automatically.",
    },
    {
        "value": "claude_local",
        "label": "Claude Code (local CLI)",
        "description": "Use the local Claude CLI if available.",
    },
    {
        "value": "openai_cli",
        "label": "OpenAI CLI (local session)",
        "description": "Use OpenAI CLI session if available.",
    },
    {
        "value": "claude_api",
        "label": "Claude API",
        "description": "Use Anthropic API key.",
    },
    {
        "value": "openai",
        "label": "OpenAI API",
        "description": "Use OpenAI API key.",
    },
    {
        "value": "ollama",
        "label": "Ollama (local)",
        "description": "Use local Ollama runtime.",
    },
    {
      "value": DEFAULT_FREE_MODEL,
      "label": "Mimo Flash v2 Free (default)",
      "description": "Default free fallback when no other provider is selected.",
    },
    {
      "value": "openrouter_grok4_fast",
      "label": "OpenRouter Grok4 Fast",
      "description": "High-speed Grok4 via OpenRouter for quick fixes.",
    },
  ]


@dataclass
class AIResponse:
    """AI response with metadata."""
    content: str
    provider: AIProvider
    model: str
    success: bool
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None


@dataclass
class ProviderSelection:
    provider: Optional[AIProvider]
    model: Optional[str]
    strict_preferred: bool
    label: str


def resolve_provider_selection(
    provider_name: Optional[str],
    model_name: Optional[str],
) -> ProviderSelection:
    normalized = (provider_name or "").strip().lower()
    model_value = (model_name or "").strip() or DEFAULT_FREE_MODEL

    if normalized in {
        "grok4_fast",
        "grok4",
        "openrouter_grok4_fast",
    }:
        return ProviderSelection(
            provider=AIProvider.FREE_ALTERNATIVE,
            model=GROK4_FAST_MODEL,
            strict_preferred=True,
            label="openrouter_grok4_fast",
        )

    if not normalized or normalized in {
        "default",
        DEFAULT_FREE_MODEL,
        "free",
        "free_alternative",
        "mimo_flash_v2_free",
    }:
        return ProviderSelection(
            provider=AIProvider.FREE_ALTERNATIVE,
            model=DEFAULT_FREE_MODEL,
            strict_preferred=True,
            label=DEFAULT_FREE_MODEL,
        )

    if normalized in {"auto", "automatic"}:
        return ProviderSelection(
            provider=None,
            model=model_value,
            strict_preferred=False,
            label="auto",
        )

    provider_map = {
        "claude_local": AIProvider.CLAUDE_LOCAL,
        "claude_api": AIProvider.CLAUDE_API,
        "openai_cli": AIProvider.OPENAI_CLI,
        "openai": AIProvider.OPENAI,
        "ollama": AIProvider.OLLAMA,
    }

    provider = provider_map.get(normalized)
    if provider is None:
        return ProviderSelection(
            provider=None,
            model=model_value,
            strict_preferred=False,
            label="auto",
        )

    return ProviderSelection(
        provider=provider,
        model=model_value,
        strict_preferred=False,
        label=provider.value,
    )


class AIClient:
    """
    Multi-provider AI client with automatic fallback.
    
    Fallback chain:
    1. Claude Code (local auth if available)
    2. OpenAI CLI session (if logged in)
    3. Claude API (if API key available)
    4. GPT-4 Turbo API (if key available)
    5. Optional Ollama local runtime
    6. Free alternative prompts (include OpenRouter Mimo Flash / offline Ollama guidance)
    """
    
    def __init__(self) -> None:
        self.config = get_config()
        self.paths = get_actifix_paths()
        self._claude_local_available = None
        self._openai_cli_logged_in = None
        self._api_keys_checked = False
        
    def generate_fix(
        self,
        ticket_info: Dict[str, Any],
        max_retries: int = 3,
        preferred_provider: Optional[AIProvider] = None,
        preferred_model: Optional[str] = None,
        strict_preferred: bool = False,
    ) -> AIResponse:
        """
        Generate a fix for the given ticket using AI.
        
        Args:
            ticket_info: Ticket information dict
            max_retries: Maximum retry attempts per provider
            preferred_provider: Optional preferred provider to try first
        
        Returns:
            AIResponse with fix content or error
        """
        # Build the prompt
        prompt = self._build_fix_prompt(ticket_info)
        
        # Determine provider order
        providers = self._get_provider_order(preferred_provider, strict_preferred=strict_preferred)

        # Collect all errors instead of overwriting
        all_errors = []

        for provider in providers:
            if provider == AIProvider.OPENAI_CLI:
                response = self._call_openai_cli(prompt)
                if response.success:
                    return response
                all_errors.append(f"{provider.value}: {response.error or 'OpenAI CLI failed'}")
                continue

            # Log attempt (database is canonical, no text files)
            # log_event removed as database is the canonical storage

            for attempt in range(max_retries):
                try:
                    response = self._call_provider(
                        provider,
                        prompt,
                        ticket_info,
                        preferred_model=preferred_model,
                    )
                    if response.success:
                        # Log success (database is canonical, no text files)
                        # log_event removed as database is the canonical storage
                        return response
                    else:
                        if response.error:
                            all_errors.append(f"{provider.value}: {response.error}")
                        # Log failure (database is canonical, no text files)
                        # log_event removed as database is the canonical storage

                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)  # Exponential backoff

                except Exception as e:
                    all_errors.append(f"{provider.value} (attempt {attempt + 1}): {str(e)}")
                    # Log exception (database is canonical, no text files)
                    # log_event removed as database is the canonical storage

                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)

        # All providers failed
        last_error = "; ".join(all_errors) if all_errors else "All AI providers failed"
        return AIResponse(
            content="",
            provider=AIProvider.FREE_ALTERNATIVE,
            model="none",
            success=False,
            error=f"All AI providers failed. Last error: {last_error}"
        )
    
    def _get_provider_order(
        self,
        preferred: Optional[AIProvider] = None,
        strict_preferred: bool = False,
    ) -> List[AIProvider]:
        """Get ordered list of providers to try."""
        providers = []
        
        # Add preferred provider first if specified
        if preferred:
            providers.append(preferred)

        if strict_preferred and preferred:
            if preferred != AIProvider.FREE_ALTERNATIVE:
                providers.append(AIProvider.FREE_ALTERNATIVE)
            return providers
        
        # Add Claude local if available
        if self._is_claude_local_available():
            if AIProvider.CLAUDE_LOCAL not in providers:
                providers.append(AIProvider.CLAUDE_LOCAL)
        
        # Add OpenAI CLI if logged in
        if self._is_openai_cli_logged_in():
            if AIProvider.OPENAI_CLI not in providers:
                providers.append(AIProvider.OPENAI_CLI)
        
        # Add Claude API if key available
        if self._has_claude_api_key():
            if AIProvider.CLAUDE_API not in providers:
                providers.append(AIProvider.CLAUDE_API)
        
        # Add OpenAI if key available
        if self._has_openai_api_key():
            if AIProvider.OPENAI not in providers:
                providers.append(AIProvider.OPENAI)
        
        # Add Ollama if available
        if self._is_ollama_available():
            if AIProvider.OLLAMA not in providers:
                providers.append(AIProvider.OLLAMA)
        
        # Always add free alternative as last resort
        if AIProvider.FREE_ALTERNATIVE not in providers:
            providers.append(AIProvider.FREE_ALTERNATIVE)
        
        return providers

    def get_status(self, selection: ProviderSelection) -> Dict[str, Any]:
        """Return provider status for UI dashboards."""
        provider_order = self._get_provider_order(
            selection.provider,
            strict_preferred=selection.strict_preferred,
        )
        providers = []
        active_provider = None

        for provider in provider_order:
            available = self._provider_available(provider)
            providers.append({
                "provider": provider.value,
                "available": available,
            })
            if active_provider is None and available:
                active_provider = provider

        if active_provider is None:
            active_provider = AIProvider.FREE_ALTERNATIVE

        active_provider_value = (
            selection.model or DEFAULT_FREE_MODEL
            if active_provider == AIProvider.FREE_ALTERNATIVE
            else active_provider.value
        )

        return {
            "preferred_provider": selection.label,
            "preferred_model": selection.model or "",
            "active_provider": active_provider_value,
            "active_model": self._default_model_for(active_provider, selection),
            "provider_order": [provider.value for provider in provider_order],
            "providers": providers,
            "provider_options": AI_PROVIDER_OPTIONS,
        }

    def _provider_available(self, provider: AIProvider) -> bool:
        if provider == AIProvider.CLAUDE_LOCAL:
            return self._is_claude_local_available()
        if provider == AIProvider.OPENAI_CLI:
            return self._is_openai_cli_logged_in()
        if provider == AIProvider.CLAUDE_API:
            return self._has_claude_api_key()
        if provider == AIProvider.OPENAI:
            return self._has_openai_api_key()
        if provider == AIProvider.OLLAMA:
            return self._is_ollama_available()
        if provider == AIProvider.FREE_ALTERNATIVE:
            return True
        return False

    def _default_model_for(
        self,
        provider: AIProvider,
        selection: ProviderSelection,
    ) -> str:
        if provider == AIProvider.CLAUDE_LOCAL:
            return "claude-3-sonnet"
        if provider == AIProvider.CLAUDE_API:
            return "claude-3-5-sonnet-20241022"
        if provider == AIProvider.OPENAI_CLI:
            return "gpt-4-turbo-preview"
        if provider == AIProvider.OPENAI:
            return "gpt-4-turbo-preview"
        if provider == AIProvider.OLLAMA:
            return self.config.ollama_model
        if provider == AIProvider.FREE_ALTERNATIVE:
            return selection.model or DEFAULT_FREE_MODEL
        return "unknown"
    
    def _call_provider(
        self,
        provider: AIProvider,
        prompt: str,
        ticket_info: Dict[str, Any],
        preferred_model: Optional[str] = None,
    ) -> AIResponse:
        """Call specific AI provider with rate limiting."""
        # Validate provider is a valid AIProvider enum
        if not isinstance(provider, AIProvider):
            return AIResponse(
                content="",
                provider=provider,
                model="unknown",
                success=False,
                error=f"Unknown provider: {provider}"
            )

        # Check rate limits before making API calls
        rate_limiter = get_rate_limiter()
        provider_key = provider.value

        try:
            rate_limiter.check_rate_limit(provider_key)
        except RateLimitError as e:
            response = AIResponse(
                content="",
                provider=provider,
                model="unknown",
                success=False,
                error=str(e)
            )
            # Record rate limit violation
            rate_limiter.record_call(
                provider_key,
                success=False,
                error=f"Rate limit exceeded: {e}"
            )
            return response

        # Call the appropriate provider
        try:
            if provider == AIProvider.CLAUDE_LOCAL:
                response = self._call_claude_local(prompt, ticket_info)
            elif provider == AIProvider.CLAUDE_API:
                response = self._call_claude_api(prompt, ticket_info)
            elif provider == AIProvider.OPENAI:
                response = self._call_openai(prompt, ticket_info)
            elif provider == AIProvider.OLLAMA:
                response = self._call_ollama(prompt, ticket_info)
            elif provider == AIProvider.FREE_ALTERNATIVE:
                response = self._call_free_alternative(prompt, ticket_info, preferred_model)
            else:
                response = AIResponse(
                    content="",
                    provider=provider,
                    model="unknown",
                    success=False,
                    error=f"Unknown provider: {provider}"
                )

            # Record the API call
            rate_limiter.record_call(
                provider_key,
                success=response.success,
                tokens_used=response.tokens_used,
                cost_usd=response.cost_usd,
                error=response.error if not response.success else None
            )

            return response

        except Exception as e:
            # Record failure
            rate_limiter.record_call(
                provider_key,
                success=False,
                error=str(e)
            )
            raise
    
    def _call_claude_local(self, prompt: str, ticket_info: Dict[str, Any]) -> AIResponse:
        """Call Claude using local CLI (if logged in)."""
        try:
            timeout_seconds = 10 if os.getenv("PYTEST_CURRENT_TEST") else 300
            # Try to use Claude CLI
            result = subprocess.run(
                ["claude", "--no-stream"],
                input=prompt,
                text=True,
                capture_output=True,
                timeout=timeout_seconds
            )
            
            if result.returncode == 0:
                return AIResponse(
                    content=result.stdout.strip(),
                    provider=AIProvider.CLAUDE_LOCAL,
                    model="claude-3-sonnet",
                    success=True
                )
            else:
                return AIResponse(
                    content="",
                    provider=AIProvider.CLAUDE_LOCAL,
                    model="claude-3-sonnet",
                    success=False,
                    error=f"Claude CLI failed: {result.stderr}"
                )
                
        except subprocess.TimeoutExpired:
            return AIResponse(
                content="",
                provider=AIProvider.CLAUDE_LOCAL,
                model="claude-3-sonnet",
                success=False,
                error="Claude CLI timeout"
            )
        except FileNotFoundError:
            return AIResponse(
                content="",
                provider=AIProvider.CLAUDE_LOCAL,
                model="claude-3-sonnet",
                success=False,
                error="Claude CLI not found"
            )
        except Exception as e:
            return AIResponse(
                content="",
                provider=AIProvider.CLAUDE_LOCAL,
                model="claude-3-sonnet",
                success=False,
                error=f"Claude CLI error: {e}"
            )
    
    def _call_claude_api(self, prompt: str, ticket_info: Dict[str, Any]) -> AIResponse:
        """Call Claude using Anthropic API."""
        try:
            import anthropic
            
            api_key = os.environ.get("ANTHROPIC_API_KEY") or self.config.ai_api_key
            if not api_key:
                return AIResponse(
                    content="",
                    provider=AIProvider.CLAUDE_API,
                    model="claude-3-sonnet",
                    success=False,
                    error="No Anthropic API key found"
                )
            
            client = anthropic.Anthropic(api_key=api_key)

            # TODO: Make model configurable via config
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return AIResponse(
                content=response.content[0].text,
                provider=AIProvider.CLAUDE_API,
                model="claude-3-5-sonnet-20241022",
                success=True,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                cost_usd=self._estimate_claude_cost(response.usage.input_tokens, response.usage.output_tokens)
            )
            
        except ImportError:
            return AIResponse(
                content="",
                provider=AIProvider.CLAUDE_API,
                model="claude-3-sonnet",
                success=False,
                error="anthropic package not installed"
            )
        except Exception as e:
            return AIResponse(
                content="",
                provider=AIProvider.CLAUDE_API,
                model="claude-3-sonnet",
                success=False,
                error=f"Anthropic API error: {e}"
            )
    
    def _call_openai_cli(self, prompt: str) -> AIResponse:
        """Call OpenAI via CLI when available."""
        if shutil.which("openai") is None:
            return AIResponse(
                content="",
                provider=AIProvider.OPENAI_CLI,
                model="gpt-4-turbo-preview",
                success=False,
                error="OpenAI CLI not found",
            )

        return AIResponse(
            content="",
            provider=AIProvider.OPENAI_CLI,
            model="gpt-4-turbo-preview",
            success=False,
            error="OpenAI CLI not configured for automated calls",
        )

    def _call_openai(self, prompt: str, ticket_info: Dict[str, Any]) -> AIResponse:
        """Call OpenAI GPT-4 Turbo."""
        try:
            import openai
            
            api_key = os.environ.get("OPENAI_API_KEY") or self.config.ai_api_key
            if not api_key:
                return AIResponse(
                    content="",
                    provider=AIProvider.OPENAI,
                    model="gpt-4-turbo",
                    success=False,
                    error="No OpenAI API key found"
                )
            
            client = openai.OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.1
            )
            
            return AIResponse(
                content=response.choices[0].message.content,
                provider=AIProvider.OPENAI,
                model="gpt-4-turbo",
                success=True,
                tokens_used=response.usage.total_tokens,
                cost_usd=self._estimate_openai_cost(response.usage.prompt_tokens, response.usage.completion_tokens)
            )
            
        except ImportError:
            return AIResponse(
                content="",
                provider=AIProvider.OPENAI,
                model="gpt-4-turbo",
                success=False,
                error="openai package not installed"
            )
        except Exception as e:
            return AIResponse(
                content="",
                provider=AIProvider.OPENAI,
                model="gpt-4-turbo",
                success=False,
                error=f"OpenAI API error: {e}"
            )
    
    def _call_ollama(self, prompt: str, ticket_info: Dict[str, Any]) -> AIResponse:
        """Call local Ollama instance."""
        ollama_model = self.config.ollama_model

        try:
            import requests

            timeout_seconds = 10 if os.getenv("PYTEST_CURRENT_TEST") else 300
            # Try to connect to local Ollama
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=timeout_seconds
            )

            if response.status_code == 200:
                result = response.json()
                return AIResponse(
                    content=result.get("response", ""),
                    provider=AIProvider.OLLAMA,
                    model=ollama_model,
                    success=True,
                    cost_usd=0.0  # Free local model
                )
            else:
                return AIResponse(
                    content="",
                    provider=AIProvider.OLLAMA,
                    model=ollama_model,
                    success=False,
                    error=f"Ollama HTTP {response.status_code}"
                )

        except ImportError:
            return AIResponse(
                content="",
                provider=AIProvider.OLLAMA,
                model=ollama_model,
                success=False,
                error="requests package not installed"
            )
        except Exception as e:
            return AIResponse(
                content="",
                provider=AIProvider.OLLAMA,
                model=ollama_model,
                success=False,
                error=f"Ollama error: {e}"
            )

    def _call_openrouter(self, prompt: str, ticket_info: Dict[str, Any], model: str) -> AIResponse:
        """Call OpenRouter API (OpenAI-compatible endpoint)."""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return AIResponse(
                content="",
                provider=AIProvider.FREE_ALTERNATIVE,
                model=model,
                success=False,
                error="OPENROUTER_API_KEY not set. Falling back to manual prompt."
            )
        try:
            import openai
            model_id = model.split("/", 1)[1] if "/" in model else model
            client = openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            response = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.1
            )
            content = response.choices[0].message.content or ""
            input_tokens = getattr(response.usage, 'prompt_tokens', 0)
            output_tokens = getattr(response.usage, 'completion_tokens', 0)
            tokens_used = input_tokens + output_tokens
            cost_usd = self._estimate_openai_cost(input_tokens, output_tokens)
            return AIResponse(
                content=content,
                provider=AIProvider.FREE_ALTERNATIVE,
                model=model,
                success=True,
                tokens_used=tokens_used,
                cost_usd=cost_usd
            )
        except ImportError:
            return AIResponse(
                content="",
                provider=AIProvider.FREE_ALTERNATIVE,
                model=model,
                success=False,
                error="openai package not installed"
            )
        except Exception as e:
            return AIResponse(
                content="",
                provider=AIProvider.FREE_ALTERNATIVE,
                model=model,
                success=False,
                error=f"OpenRouter API error: {str(e)}"
            )

    def _call_free_alternative(
        self,
        prompt: str,
        ticket_info: Dict[str, Any],
        preferred_model: Optional[str] = None,
    ) -> AIResponse:
        model = preferred_model or DEFAULT_FREE_MODEL
        if "openrouter" in model.lower() and os.environ.get("OPENROUTER_API_KEY"):
            return self._call_openrouter(prompt, ticket_info, model)
        """Prompt user to choose a free alternative (fallback)."""
        if os.getenv("ACTIFIX_NONINTERACTIVE") == "1" or not sys.stdin.isatty():
            return AIResponse(
                content="",
                provider=AIProvider.FREE_ALTERNATIVE,
                model=model,
                success=False,
                error="Non-interactive session: free alternative prompt disabled",
            )
        default_model = model
        print("\n" + "="*60)
        print("🤖 AI ASSISTANCE NEEDED")
        print("="*60)
        print(f"Ticket: {ticket_info.get('id', 'Unknown')}")
        print(f"Error: {ticket_info.get('message', 'Unknown error')}")
        print(f"Source: {ticket_info.get('source', 'Unknown')}")
        print("\nAll automated AI providers failed. Please choose a free alternative:")
        print(f"\n1. Use {default_model} (OpenRouter)")
        print("2. Use Claude.ai (web interface)")
        print("3. Use ChatGPT (web interface)")
        print("4. Use local Ollama (if installed)")
        print("5. Manual fix (provide solution)")
        print("6. Skip this ticket")
        
        while True:
            try:
                choice = input("\nEnter your choice (1-6): ").strip()
                
                if choice == "1":
                    print(f"\n📋 Copy this prompt to OpenRouter ({default_model}):")
                    print("-" * 40)
                    print(prompt)
                    print("-" * 40)
                    solution = input("\nPaste the response here: ").strip()
                    if solution:
                        return AIResponse(
                            content=solution,
                            provider=AIProvider.FREE_ALTERNATIVE,
                            model=default_model,
                            success=True,
                            cost_usd=0.0
                        )
                
                elif choice == "2":
                    print("\n📋 Copy this prompt to Claude.ai:")
                    print("-" * 40)
                    print(prompt)
                    print("-" * 40)
                    solution = input("\nPaste Claude's response here: ").strip()
                    if solution:
                        return AIResponse(
                            content=solution,
                            provider=AIProvider.FREE_ALTERNATIVE,
                            model="claude-web",
                            success=True,
                            cost_usd=0.0
                        )
                
                elif choice == "3":
                    print("\n📋 Copy this prompt to ChatGPT:")
                    print("-" * 40)
                    print(prompt)
                    print("-" * 40)
                    solution = input("\nPaste ChatGPT's response here: ").strip()
                    if solution:
                        return AIResponse(
                            content=solution,
                            provider=AIProvider.FREE_ALTERNATIVE,
                            model="chatgpt-web",
                            success=True,
                            cost_usd=0.0
                        )
                
                elif choice == "4":
                    # Try Ollama again
                    return self._call_ollama(prompt, ticket_info)
                
                elif choice == "5":
                    print("\nProvide your manual fix:")
                    solution = input("Solution: ").strip()
                    if solution:
                        return AIResponse(
                            content=solution,
                            provider=AIProvider.FREE_ALTERNATIVE,
                            model="manual",
                            success=True,
                            cost_usd=0.0
                        )
                
                elif choice == "6":
                    return AIResponse(
                        content="",
                        provider=AIProvider.FREE_ALTERNATIVE,
                        model="skipped",
                        success=False,
                        error="User chose to skip ticket"
                    )
                
                else:
                    print("Invalid choice. Please enter 1-6.")
                    
            except KeyboardInterrupt:
                return AIResponse(
                    content="",
                    provider=AIProvider.FREE_ALTERNATIVE,
                    model="interrupted",
                    success=False,
                    error="User interrupted free alternative flow",
                )
    
    def _build_fix_prompt(self, ticket_info: Dict[str, Any]) -> str:
        """Build the AI prompt for fixing the ticket."""
        return f"""You are an expert software engineer helping to fix a bug in the Actifix error tracking system.

TICKET INFORMATION:
- ID: {ticket_info.get('id', 'Unknown')}
- Priority: {ticket_info.get('priority', 'Unknown')}
- Error Type: {ticket_info.get('error_type', 'Unknown')}
- Message: {ticket_info.get('message', 'Unknown')}
- Source: {ticket_info.get('source', 'Unknown')}
- Stack Trace: {ticket_info.get('stack_trace', 'Not available')}

CONTEXT:
This is a Python project using the Actifix framework for automated error tracking and remediation. The error occurred during normal operation and needs to be fixed.

TASK:
1. Analyze the error and identify the root cause
2. Provide a specific, actionable fix
3. Include any code changes needed
4. Explain why this fix will resolve the issue
5. Suggest any tests that should be added

Please provide a clear, concise solution that can be implemented immediately.

RESPONSE FORMAT:
## Analysis
[Your analysis of the root cause]

## Solution
[Step-by-step fix instructions]

## Code Changes
```python
# Any specific code changes needed
```

## Testing
[Suggested tests or validation steps]

## Explanation
[Why this fix resolves the issue]
"""
    
    def _is_claude_local_available(self) -> bool:
        """Check if Claude CLI is available and logged in."""
        if self._claude_local_available is not None:
            return self._claude_local_available
        
        try:
            # Check if claude command exists and user is logged in
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            self._claude_local_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._claude_local_available = False
        
        return self._claude_local_available

    def _is_openai_cli_logged_in(self) -> bool:
        """Check if OpenAI CLI is available and configured."""
        if self._openai_cli_logged_in is not None:
            return self._openai_cli_logged_in

        if shutil.which("openai") is None:
            self._openai_cli_logged_in = False
            return self._openai_cli_logged_in

        self._openai_cli_logged_in = bool(
            os.environ.get("OPENAI_API_KEY") or self.config.ai_api_key
        )
        return self._openai_cli_logged_in
    
    def _has_claude_api_key(self) -> bool:
        """Check if Anthropic API key is available."""
        return bool(os.environ.get("ANTHROPIC_API_KEY") or self.config.ai_api_key)
    
    def _has_openai_api_key(self) -> bool:
        """Check if OpenAI API key is available."""
        return bool(os.environ.get("OPENAI_API_KEY") or self.config.ai_api_key)
    
    def _is_ollama_available(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _estimate_claude_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for Claude API usage."""
        # Claude 3 Sonnet pricing (as of 2024)
        input_cost = input_tokens * 0.000003  # $3 per 1M input tokens
        output_cost = output_tokens * 0.000015  # $15 per 1M output tokens
        return input_cost + output_cost
    
    def _estimate_openai_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for OpenAI API usage."""
        # GPT-4 Turbo pricing (as of 2024)
        input_cost = input_tokens * 0.00001  # $10 per 1M input tokens
        output_cost = output_tokens * 0.00003  # $30 per 1M output tokens
        return input_cost + output_cost


# Global AI client instance
_global_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """Get or create the global AI client."""
    global _global_client
    if _global_client is None:
        _global_client = AIClient()
    return _global_client


def reset_ai_client() -> None:
    """Reset the global AI client (for testing)."""
    global _global_client
    _global_client = None