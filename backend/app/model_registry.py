from __future__ import annotations

from dataclasses import asdict, dataclass
import os


PLACEHOLDER_VALUES = {
    "your_key_here",
    "your_openai_key",
    "your_anthropic_key",
    "your_google_key",
    "your_groq_key",
    "your_minimax_key",
    "your_moonshot_key",
    "changeme",
    "change_me",
    "none",
    "null",
    "false",
}


def env_secret(env_name: str) -> str | None:
    value = os.getenv(env_name, "").strip()
    if not value:
        return None
    if value.lower() in PLACEHOLDER_VALUES:
        return None
    return value


@dataclass(frozen=True)
class SupportedModel:
    name: str
    provider: str
    provider_label: str
    api_key_env: str
    litellm_model: str

    @property
    def configured(self) -> bool:
        if self.provider == "mock":
            return os.getenv(self.api_key_env, "false").strip().lower() == "true"
        return env_secret(self.api_key_env) is not None

    @property
    def api_key(self) -> str | None:
        return env_secret(self.api_key_env)

    def public_dict(self, *, configured: bool | None = None) -> dict:
        payload = asdict(self)
        payload["configured"] = self.configured if configured is None else configured
        return payload


MODEL_MAP: dict[str, SupportedModel] = {
    "gpt-5.4-pro": SupportedModel(
        "gpt-5.4-pro", "openai", "OpenAI", "OPENAI_API_KEY", "gpt-5.4-pro"
    ),
    "gpt-5.4-mini": SupportedModel(
        "gpt-5.4-mini", "openai", "OpenAI", "OPENAI_API_KEY", "gpt-5.4-mini"
    ),
    "gpt-4o": SupportedModel("gpt-4o", "openai", "OpenAI", "OPENAI_API_KEY", "gpt-4o"),
    "gpt-4o-mini": SupportedModel(
        "gpt-4o-mini", "openai", "OpenAI", "OPENAI_API_KEY", "gpt-4o-mini"
    ),
    "claude-opus-4-6": SupportedModel(
        "claude-opus-4-6",
        "anthropic",
        "Anthropic",
        "ANTHROPIC_API_KEY",
        "anthropic/claude-opus-4-6",
    ),
    "claude-sonnet-4-6": SupportedModel(
        "claude-sonnet-4-6",
        "anthropic",
        "Anthropic",
        "ANTHROPIC_API_KEY",
        "anthropic/claude-sonnet-4-6",
    ),
    "claude-haiku-4-5": SupportedModel(
        "claude-haiku-4-5",
        "anthropic",
        "Anthropic",
        "ANTHROPIC_API_KEY",
        "anthropic/claude-haiku-4-5",
    ),
    "claude-3.5-sonnet": SupportedModel(
        "claude-3.5-sonnet",
        "anthropic",
        "Anthropic",
        "ANTHROPIC_API_KEY",
        "anthropic/claude-3.5-sonnet",
    ),
    "gemini-3.1-pro": SupportedModel(
        "gemini-3.1-pro",
        "google",
        "Google",
        "GOOGLE_API_KEY",
        "gemini/gemini-3.1-pro",
    ),
    "gemini-3-flash": SupportedModel(
        "gemini-3-flash",
        "google",
        "Google",
        "GOOGLE_API_KEY",
        "gemini/gemini-3-flash",
    ),
    "gemini-2.5-flash-lite": SupportedModel(
        "gemini-2.5-flash-lite",
        "google",
        "Google",
        "GOOGLE_API_KEY",
        "gemini/gemini-2.5-flash-lite",
    ),
    "llama-4-maverick": SupportedModel(
        "llama-4-maverick",
        "groq",
        "Llama via Groq",
        "GROQ_API_KEY",
        "groq/llama-4-maverick",
    ),
    "llama-4-scout": SupportedModel(
        "llama-4-scout",
        "groq",
        "Llama via Groq",
        "GROQ_API_KEY",
        "groq/llama-4-scout",
    ),
    "llama-3.3-70b": SupportedModel(
        "llama-3.3-70b",
        "groq",
        "Llama via Groq",
        "GROQ_API_KEY",
        "groq/llama-3.3-70b",
    ),
    "minimax-m2.7": SupportedModel(
        "minimax-m2.7",
        "minimax",
        "MiniMax",
        "MINIMAX_API_KEY",
        "minimax/minimax-m2.7",
    ),
    "minimax-m2.5-lightning": SupportedModel(
        "minimax-m2.5-lightning",
        "minimax",
        "MiniMax",
        "MINIMAX_API_KEY",
        "minimax/minimax-m2.5-lightning",
    ),
    "kimi-latest": SupportedModel(
        "kimi-latest",
        "moonshot",
        "Moonshot",
        "MOONSHOT_API_KEY",
        "moonshot/kimi-latest",
    ),
    "kimi-k2-thinking": SupportedModel(
        "kimi-k2-thinking",
        "moonshot",
        "Moonshot",
        "MOONSHOT_API_KEY",
        "moonshot/kimi-k2-thinking",
    ),
    "kimi-k2-turbo-preview": SupportedModel(
        "kimi-k2-turbo-preview",
        "moonshot",
        "Moonshot",
        "MOONSHOT_API_KEY",
        "moonshot/kimi-k2-turbo-preview",
    ),
    "kimi-k2.5-vision": SupportedModel(
        "kimi-k2.5-vision",
        "moonshot",
        "Moonshot",
        "MOONSHOT_API_KEY",
        "moonshot/kimi-k2.5-vision",
    ),
    "moonshot-v1-128k": SupportedModel(
        "moonshot-v1-128k",
        "moonshot",
        "Moonshot",
        "MOONSHOT_API_KEY",
        "moonshot/moonshot-v1-128k",
    ),
}

SUPPORTED_MODELS: tuple[SupportedModel, ...] = tuple(MODEL_MAP.values())
MOCK_MODEL = SupportedModel(
    "mock-debate-model",
    "mock",
    "Mock",
    "MOCK_LLM_RESPONSES",
    "mock-debate-model",
)


PROVIDER_ORDER = ("openai", "anthropic", "google", "groq", "minimax", "moonshot")


def all_models() -> list[SupportedModel]:
    return list(SUPPORTED_MODELS)


def available_models() -> list[SupportedModel]:
    return [model for model in SUPPORTED_MODELS if model.configured]


def get_model(model_name: str) -> SupportedModel | None:
    return MODEL_MAP.get(model_name)


def get_available_model(model_name: str) -> SupportedModel | None:
    model = get_model(model_name)
    if model and model.configured:
        return model
    return None


def available_model_payloads(*, include_mock: bool = False) -> list[dict]:
    payloads = [model.public_dict() for model in available_models()]
    if include_mock:
        payloads.insert(0, MOCK_MODEL.public_dict(configured=True))
    return payloads


def provider_summaries(*, unlocked_only: bool = True) -> list[dict]:
    summaries = []
    for provider in PROVIDER_ORDER:
        provider_models = [model for model in SUPPORTED_MODELS if model.provider == provider]
        if not provider_models:
            continue
        unlocked_models = [model for model in provider_models if model.configured]
        visible_models = unlocked_models if unlocked_only else provider_models
        summaries.append(
            {
                "provider": provider,
                "provider_label": provider_models[0].provider_label,
                "api_key_env": provider_models[0].api_key_env,
                "configured": provider_models[0].configured,
                "unlocked_model_count": len(unlocked_models),
                "total_model_count": len(provider_models),
                "models": [model.public_dict() for model in visible_models],
            }
        )
    return summaries
