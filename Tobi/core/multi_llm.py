"""
Multi-provider LLM router. Extends TobiLLM with GPT, Gemini, and Grok backends.

Each provider is lazy-loaded and only initialized when its API key is present.
The router picks the best provider per request based on task type, cost, and
availability. Claude remains the primary; others are used for specific tasks
or when Claude is unavailable.
"""
import logging
import time
from typing import AsyncGenerator, Optional

from Tobi.config import settings

logger = logging.getLogger("Tobi.multi_llm")


class ProviderConfig:
    """Configuration for a single LLM provider."""

    def __init__(
        self,
        name: str,
        models: dict[str, str],
        api_key_env: str,
        pricing: dict[str, dict] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.5,
    ):
        self.name = name
        self.models = models  # tier -> model name
        self.api_key_env = api_key_env
        self.pricing = pricing or {}
        self.max_tokens = max_tokens
        self.temperature = temperature

    @property
    def api_key(self) -> str:
        return getattr(settings, self.api_key_env, "") or ""

    @property
    def available(self) -> bool:
        return bool(self.api_key)


# Provider registry
PROVIDERS: dict[str, ProviderConfig] = {
    "openai": ProviderConfig(
        name="openai",
        models={
            "fast": "gpt-4o-mini",
            "brain": "gpt-4o",
            "deep": "gpt-4o",
        },
        api_key_env="OPENAI_API_KEY",
        pricing={
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4o": {"input": 2.50, "output": 10.00},
        },
    ),
    "gemini": ProviderConfig(
        name="gemini",
        models={
            "fast": "gemini-2.0-flash",
            "brain": "gemini-2.5-flash",
            "deep": "gemini-2.5-pro",
        },
        api_key_env="GEMINI_API_KEY",
        pricing={
            "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
            "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
            "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
        },
    ),
    "grok": ProviderConfig(
        name="grok",
        models={
            "fast": "grok-3-mini",
            "brain": "grok-3",
            "deep": "grok-3",
        },
        api_key_env="GROK_API_KEY",
        pricing={
            "grok-3-mini": {"input": 0.30, "output": 0.50},
            "grok-3": {"input": 3.00, "output": 15.00},
        },
    ),
}

# Task-type routing preferences
TASK_PROVIDER_MAP = {
    "code": ["claude", "openai", "gemini"],
    "research": ["claude", "gemini", "openai"],
    "creative": ["claude", "openai", "grok"],
    "quick": ["openai", "gemini", "claude"],
    "news": ["grok", "gemini", "openai"],
    "analysis": ["claude", "gemini", "openai"],
    "chat": ["claude", "openai", "gemini"],
}


def detect_task_type(message: str) -> str:
    """Classify a message into a task type for provider routing."""
    lower = message.lower()
    code_signals = ["code", "debug", "function", "class", "api", "sql", "git", "deploy", "refactor", "bug"]
    news_signals = ["news", "trending", "what happened", "latest", "update", "market", "price", "crypto", "forex"]
    research_signals = ["research", "compare", "analyze", "explain", "how does", "why", "difference between"]
    creative_signals = ["write", "draft", "story", "creative", "brainstorm", "name", "slogan"]

    code_score = sum(1 for s in code_signals if s in lower)
    news_score = sum(1 for s in news_signals if s in lower)
    research_score = sum(1 for s in research_signals if s in lower)
    creative_score = sum(1 for s in creative_signals if s in lower)

    scores = {
        "code": code_score,
        "news": news_score,
        "research": research_score,
        "creative": creative_score,
    }
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "quick"
    return best


def select_provider(task_type: str = "chat", preferred: str = "") -> str:
    """Select the best available provider for a task type."""
    if preferred and preferred in PROVIDERS and PROVIDERS[preferred].available:
        return preferred

    # Claude is always first choice if available
    if settings.ANTHROPIC_API_KEY:
        return "claude"

    ranking = TASK_PROVIDER_MAP.get(task_type, TASK_PROVIDER_MAP["chat"])
    for provider_name in ranking:
        if provider_name == "claude":
            continue  # Already checked above
        if provider_name in PROVIDERS and PROVIDERS[provider_name].available:
            return provider_name

    return "ollama"


class MultiProviderLLM:
    """Unified interface for calling multiple LLM providers."""

    def __init__(self):
        self._clients: dict[str, object] = {}
        self._initialized: dict[str, bool] = {}

    def _get_openai_client(self):
        if "openai" in self._clients:
            return self._clients["openai"]
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self._clients["openai"] = client
            self._initialized["openai"] = True
            return client
        except ImportError:
            logger.warning("openai package not installed.")
            return None
        except Exception as e:
            logger.error("OpenAI init failed: %s", e)
            return None

    def _get_gemini_client(self):
        if "gemini" in self._clients:
            return self._clients["gemini"]
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._clients["gemini"] = genai
            self._initialized["gemini"] = True
            return genai
        except ImportError:
            logger.warning("google-generativeai package not installed.")
            return None
        except Exception as e:
            logger.error("Gemini init failed: %s", e)
            return None

    def _get_grok_client(self):
        if "grok" in self._clients:
            return self._clients["grok"]
        try:
            import openai
            client = openai.AsyncOpenAI(
                api_key=settings.GROK_API_KEY,
                base_url="https://api.x.ai/v1",
            )
            self._clients["grok"] = client
            self._initialized["grok"] = True
            return client
        except ImportError:
            logger.warning("openai package required for Grok.")
            return None
        except Exception as e:
            logger.error("Grok init failed: %s", e)
            return None

    async def chat(
        self,
        message: str,
        provider: str = "",
        tier: str = "brain",
        system_prompt: str = "",
        conversation_history: list[dict] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Send a chat message to a specific provider or auto-select."""
        task_type = detect_task_type(message)
        provider = select_provider(task_type, preferred=provider)

        if provider == "claude":
            return None  # Let the main TobiLLM handle Claude

        if provider == "ollama":
            return None  # Let the main TobiLLM handle Ollama

        config = PROVIDERS.get(provider)
        if not config or not config.available:
            logger.warning("Provider %s not available, falling back.", provider)
            return None

        model = config.models.get(tier, config.models["brain"])
        temp = temperature if temperature is not None else config.temperature
        tokens = max_tokens or config.max_tokens

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if conversation_history:
            messages.extend(conversation_history[-10:])
        messages.append({"role": "user", "content": message})

        start = time.time()
        try:
            if provider == "openai":
                return await self._chat_openai(model, messages, temp, tokens)
            elif provider == "gemini":
                return await self._chat_gemini(model, messages, temp, tokens)
            elif provider == "grok":
                return await self._chat_grok(model, messages, temp, tokens)
        except Exception as e:
            logger.error("Provider %s chat failed: %s", provider, e)
            return None

        elapsed = time.time() - start
        logger.info("Provider %s [%s] responded in %.2fs", provider, model, elapsed)
        return None

    async def _chat_openai(self, model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
        client = self._get_openai_client()
        if client is None:
            return None
        resp = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()

    async def _chat_gemini(self, model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
        genai = self._get_gemini_client()
        if genai is None:
            return None
        # Extract system prompt and user messages
        system = ""
        user_msgs = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                user_msgs.append(m["content"])

        gemini_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system if system else None,
        )
        chat = gemini_model.start_chat(history=[])
        resp = await chat.send_message_async(
            "\n".join(user_msgs),
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return resp.text.strip()

    async def _chat_grok(self, model: str, messages: list[dict], temperature: float, max_tokens: int) -> str:
        client = self._get_grok_client()
        if client is None:
            return None
        resp = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()

    async def chat_stream(
        self,
        message: str,
        provider: str = "",
        tier: str = "brain",
        system_prompt: str = "",
        conversation_history: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream a response from a provider."""
        task_type = detect_task_type(message)
        provider = select_provider(task_type, preferred=provider)

        if provider in ("claude", "ollama"):
            return  # Let main TobiLLM handle

        config = PROVIDERS.get(provider)
        if not config or not config.available:
            return

        model = config.models.get(tier, config.models["brain"])

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if conversation_history:
            messages.extend(conversation_history[-10:])
        messages.append({"role": "user", "content": message})

        try:
            if provider in ("openai", "grok"):
                client = self._get_openai_client() if provider == "openai" else self._get_grok_client()
                if client:
                    stream = await client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                        stream=True,
                    )
                    async for chunk in stream:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error("Provider %s stream failed: %s", provider, e)

    def get_available_providers(self) -> list[dict]:
        """Return list of available providers and their status."""
        result = []
        for name, config in PROVIDERS.items():
            result.append({
                "name": name,
                "available": config.available,
                "models": config.models,
            })
        result.append({"name": "claude", "available": bool(settings.ANTHROPIC_API_KEY), "models": {"fast": settings.CLAUDE_FAST_MODEL, "brain": settings.CLAUDE_BRAIN_MODEL, "deep": settings.CLAUDE_DEEP_MODEL}})
        result.append({"name": "ollama", "available": True, "models": {"brain": settings.OLLAMA_MODEL}})
        return result


# Singleton
multi_llm = MultiProviderLLM()
