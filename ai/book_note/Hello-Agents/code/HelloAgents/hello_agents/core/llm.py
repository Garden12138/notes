"""Unified LLM client used by the HelloAgents learning framework."""

from __future__ import annotations

import os
from typing import Any, Dict, Generator, List, Literal
from urllib.parse import urlparse

from dotenv import load_dotenv
from openai import OpenAI

from .exceptions import HelloAgentsException


load_dotenv()

ProviderName = Literal[
    "openai",
    "deepseek",
    "qwen",
    "modelscope",
    "kimi",
    "zhipu",
    "ollama",
    "vllm",
    "local",
    "auto",
    "custom",
]

SUPPORTED_PROVIDERS = {
    "openai",
    "deepseek",
    "qwen",
    "modelscope",
    "kimi",
    "zhipu",
    "ollama",
    "vllm",
    "local",
    "auto",
    "custom",
}

_PROVIDER_ENV_PREFIX = {
    "openai": "OPENAI",
    "deepseek": "DEEPSEEK",
    "qwen": "DASHSCOPE",
    "modelscope": "MODELSCOPE",
    "kimi": "KIMI",
    "zhipu": "ZHIPU",
    "ollama": "OLLAMA",
    "vllm": "VLLM",
    "local": "LOCAL_LLM",
    "custom": "LLM",
}

_DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "modelscope": "https://api-inference.modelscope.cn/v1",
    "kimi": "https://api.moonshot.cn/v1",
    "zhipu": "https://open.bigmodel.cn/api/paas/v4",
    "ollama": "http://127.0.0.1:11434/v1",
    "vllm": "http://127.0.0.1:8000/v1",
}

_DEFAULT_MODELS = {
    "openai": "gpt-3.5-turbo",
    "deepseek": "deepseek-chat",
    "qwen": "qwen-plus",
    "modelscope": "Qwen/Qwen2.5-72B-Instruct",
    "kimi": "moonshot-v1-8k",
    "zhipu": "glm-4",
    "ollama": "qwen3:0.6b",
    "vllm": "Qwen/Qwen1.5-0.5B-Chat",
}

_PROVIDER_HOST_RULES = {
    "api.openai.com": "openai",
    "api.deepseek.com": "deepseek",
    "dashscope.aliyuncs.com": "qwen",
    "api-inference.modelscope.cn": "modelscope",
    "api.moonshot.cn": "kimi",
    "open.bigmodel.cn": "zhipu",
}


def _first_value(*values: str | None) -> str | None:
    """Return the first non-empty string."""
    for value in values:
        if value and value.strip():
            return value.strip()
    return None


class HelloAgentsLLM:
    """Call cloud or local OpenAI-compatible model services."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        provider: ProviderName | str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Resolve the provider configuration and create one shared SDK client.

        ``apiKey`` and ``baseUrl`` remain accepted through ``kwargs`` so code
        written against the earlier chapter can migrate without an immediate
        breaking change.
        """
        load_dotenv()

        api_key = _first_value(api_key, kwargs.pop("apiKey", None))
        base_url = _first_value(base_url, kwargs.pop("baseUrl", None))

        selected_provider = _first_value(
            provider,
            os.getenv("LLM_PROVIDER"),
            "auto",
        )
        assert selected_provider is not None
        selected_provider = selected_provider.lower()

        if selected_provider == "auto":
            selected_provider = self._auto_detect_provider(api_key, base_url)

        if selected_provider not in SUPPORTED_PROVIDERS - {"auto"}:
            choices = "、".join(sorted(SUPPORTED_PROVIDERS))
            raise HelloAgentsException(
                f"不支持 provider={selected_provider!r}，可选值：{choices}",
            )

        self.provider = selected_provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout or int(os.getenv("LLM_TIMEOUT", "60"))
        self.request_options = kwargs

        (
            self.model,
            self.api_key,
            self.base_url,
        ) = self._resolve_credentials(
            provider=selected_provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
        )
        self._client = self._create_client(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        # Keep the earlier chapter's public attribute available during migration.
        self.client = self._client

    def _auto_detect_provider(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> str:
        """Compatibility name from the chapter; delegates to rule inference."""
        del api_key  # Provider inference intentionally avoids key-format guessing.
        return self._infer_provider_by_rules(base_url)

    def _infer_provider_by_rules(self, base_url: str | None = None) -> str:
        """Infer a provider with deterministic configuration rules."""
        resolved_base_url = _first_value(base_url, os.getenv("LLM_BASE_URL"))
        if resolved_base_url:
            parsed = urlparse(resolved_base_url)
            hostname = (parsed.hostname or "").lower()
            if hostname in _PROVIDER_HOST_RULES:
                return _PROVIDER_HOST_RULES[hostname]
            if parsed.port == 11434:
                return "ollama"
            if parsed.port == 8000:
                return "vllm"
            return "custom"

        candidates = [
            provider
            for provider, prefix in _PROVIDER_ENV_PREFIX.items()
            if provider not in {"ollama", "vllm", "local", "custom"}
            and os.getenv(f"{prefix}_API_KEY")
        ]
        if os.getenv("OLLAMA_API_KEY") or os.getenv("OLLAMA_HOST"):
            candidates.append("ollama")
        if os.getenv("VLLM_API_KEY") or os.getenv("VLLM_HOST"):
            candidates.append("vllm")
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            joined = "、".join(candidates)
            raise HelloAgentsException(
                f"规则推断得到多个候选 provider：{joined}。"
                "请通过 provider 或 LLM_PROVIDER 显式选择。",
            )
        return "custom"

    def _resolve_credentials(
        self,
        provider: str,
        model: str | None,
        api_key: str | None,
        base_url: str | None,
    ) -> tuple[str, str, str]:
        """Resolve explicit values, provider variables, then common variables."""
        prefix = _PROVIDER_ENV_PREFIX[provider]
        provider_model = os.getenv(f"{prefix}_MODEL_ID")
        provider_api_key = os.getenv(f"{prefix}_API_KEY")
        provider_base_url = os.getenv(f"{prefix}_BASE_URL")
        if provider == "kimi":
            provider_api_key = _first_value(
                provider_api_key,
                os.getenv("MOONSHOT_API_KEY"),
            )
        elif provider == "zhipu":
            provider_api_key = _first_value(
                provider_api_key,
                os.getenv("GLM_API_KEY"),
            )
        elif provider == "ollama":
            provider_base_url = _first_value(
                provider_base_url,
                os.getenv("OLLAMA_HOST"),
            )
        elif provider == "vllm":
            provider_base_url = _first_value(
                provider_base_url,
                os.getenv("VLLM_HOST"),
            )

        resolved_model = _first_value(
            model,
            provider_model,
            os.getenv("LLM_MODEL_ID"),
            self._get_default_model(provider),
        )
        resolved_api_key = _first_value(
            api_key,
            provider_api_key,
            os.getenv("LLM_API_KEY"),
        )
        resolved_base_url = _first_value(
            base_url,
            provider_base_url,
            os.getenv("LLM_BASE_URL"),
            _DEFAULT_BASE_URLS.get(provider),
        )

        if provider in {"ollama", "vllm", "local"}:
            resolved_api_key = resolved_api_key or (
                "ollama" if provider == "ollama" else "EMPTY"
            )

        missing = [
            name
            for name, value in (
                ("模型 ID", resolved_model),
                ("API Key", resolved_api_key),
                ("服务地址", resolved_base_url),
            )
            if not value
        ]
        if missing:
            raise HelloAgentsException(
                f"provider={provider} 缺少配置：{'、'.join(missing)}。",
            )

        assert resolved_model is not None
        assert resolved_api_key is not None
        assert resolved_base_url is not None
        resolved_base_url = self._normalize_local_base_url(
            provider,
            resolved_base_url,
        )
        return resolved_model, resolved_api_key, resolved_base_url

    @staticmethod
    def _get_default_model(provider: str) -> str | None:
        """Return the chapter example model for a known provider."""
        return _DEFAULT_MODELS.get(provider)

    @staticmethod
    def _normalize_local_base_url(provider: str, base_url: str) -> str:
        """Ensure local OpenAI-compatible endpoints include the /v1 prefix."""
        normalized = base_url.rstrip("/")
        if provider in {"ollama", "vllm", "local"}:
            if not normalized.endswith("/v1"):
                normalized += "/v1"
        return normalized

    def _create_client(self, api_key: str, base_url: str) -> OpenAI:
        """Create the SDK client used by every provider branch."""
        return OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=self.timeout,
        )

    def think(
        self,
        messages: List[Dict[str, str]],
        temperature: float | None = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Stream response fragments while yielding them to the caller."""
        print(f"🧠 正在调用 {self.model} 模型...")
        request = self._build_request(
            messages=messages,
            temperature=temperature,
            stream=True,
            **kwargs,
        )

        try:
            response = self._client.chat.completions.create(**request)
            print("✅ 大语言模型响应成功:")
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                if content:
                    print(content, end="", flush=True)
                    yield content
            print()
        except Exception as error:
            raise HelloAgentsException(
                f"调用 LLM API 时发生错误：{error}",
            ) from error

    def stream_invoke(
        self,
        messages: List[Dict[str, str]],
        temperature: float | None = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Alias used by later framework components for streaming calls."""
        return self.think(messages, temperature=temperature, **kwargs)

    def invoke(
        self,
        messages: List[Dict[str, str]],
        temperature: float | None = None,
        **kwargs: Any,
    ) -> str:
        """Return one complete non-streaming response."""
        request = self._build_request(
            messages=messages,
            temperature=temperature,
            stream=False,
            **kwargs,
        )
        try:
            response = self._client.chat.completions.create(**request)
            return response.choices[0].message.content or ""
        except Exception as error:
            raise HelloAgentsException(
                f"调用 LLM API 时发生错误：{error}",
            ) from error

    def _build_request(
        self,
        messages: List[Dict[str, str]],
        temperature: float | None,
        stream: bool,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Build one Chat Completions request from shared defaults."""
        request: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": (
                self.temperature if temperature is None else temperature
            ),
            "stream": stream,
        }
        if self.max_tokens is not None:
            request["max_tokens"] = self.max_tokens
        request.update(self.request_options)
        request.update(kwargs)
        return request

    def connection_summary(self) -> str:
        """Return non-sensitive connection information."""
        return (
            f"provider={self.provider}, "
            f"model={self.model}, "
            f"base_url={self.base_url}"
        )
