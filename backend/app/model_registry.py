from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
import json
import os
import re
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from litellm import acompletion
except Exception:  # pragma: no cover - import guard for environments without LiteLLM
    acompletion = None


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
GITHUB_TOKEN_PREFIXES = ("ghp_", "github_pat_", "gho_", "ghu_", "ghs_", "ghr_")
ENABLE_GITHUB_MODELS_ENV = "ENABLE_GITHUB_MODELS"
GITHUB_MODELS_API_KEY_ENV = "GITHUB_MODELS_API_KEY"
GITHUB_MODELS_API_VERSION = "2026-03-10"
GITHUB_MODELS_CATALOG_URL = "https://models.github.ai/catalog/models"
GITHUB_MODELS_CACHE_TTL_SECONDS = 600
GITHUB_ROUTE_FAILURE_TTL_SECONDS = 21_600
GITHUB_MODEL_HINTS: dict[str, dict[str, tuple[str, ...]]] = {
    "gpt-5.4-pro": {
        "publishers": ("openai",),
        "aliases": ("gpt-5.4", "gpt 5.4", "openai/gpt-5.4", "openai gpt-5.4"),
    },
    "gpt-5.4-mini": {
        "publishers": ("openai",),
        "aliases": (
            "gpt-5.4-mini",
            "gpt 5.4 mini",
            "openai/gpt-5.4-mini",
            "openai gpt-5.4 mini",
        ),
    },
    "gpt-4o": {
        "publishers": ("openai",),
        "aliases": ("gpt-4o", "gpt 4o", "openai/gpt-4o", "openai gpt-4o"),
    },
    "gpt-4o-mini": {
        "publishers": ("openai",),
        "aliases": (
            "gpt-4o-mini",
            "gpt 4o mini",
            "openai/gpt-4o-mini",
            "openai gpt-4o mini",
        ),
    },
    "claude-opus-4-6": {
        "publishers": ("anthropic",),
        "aliases": (
            "claude-opus-4.6",
            "claude opus 4.6",
            "anthropic/claude-opus-4.6",
        ),
    },
    "claude-sonnet-4-6": {
        "publishers": ("anthropic",),
        "aliases": (
            "claude-sonnet-4.6",
            "claude sonnet 4.6",
            "anthropic/claude-sonnet-4.6",
        ),
    },
    "claude-haiku-4-5": {
        "publishers": ("anthropic",),
        "aliases": (
            "claude-haiku-4.5",
            "claude haiku 4.5",
            "anthropic/claude-haiku-4.5",
        ),
    },
    "claude-3.5-sonnet": {
        "publishers": ("anthropic",),
        "aliases": (
            "claude-3.5-sonnet",
            "claude 3.5 sonnet",
            "anthropic/claude-3.5-sonnet",
        ),
    },
    "gemini-3.1-pro": {
        "publishers": ("google",),
        "aliases": ("gemini-3.1-pro", "gemini 3.1 pro", "google/gemini-3.1-pro"),
    },
    "gemini-3-flash": {
        "publishers": ("google",),
        "aliases": ("gemini-3-flash", "gemini 3 flash", "google/gemini-3-flash"),
    },
    "gemini-2.5-flash-lite": {
        "publishers": ("google",),
        "aliases": (
            "gemini-2.5-flash-lite",
            "gemini 2.5 flash lite",
            "google/gemini-2.5-flash-lite",
        ),
    },
    "llama-4-maverick": {
        "publishers": ("meta",),
        "aliases": (
            "llama-4-maverick",
            "llama 4 maverick",
            "llama 4 maverick 17b instruct fp8",
            "meta/llama-4-maverick-17b-128e-instruct-fp8",
        ),
    },
    "llama-4-scout": {
        "publishers": ("meta",),
        "aliases": (
            "llama-4-scout",
            "llama 4 scout",
            "llama 4 scout 17b instruct",
            "meta/llama-4-scout-17b-16e-instruct",
        ),
    },
    "llama-3.3-70b": {
        "publishers": ("meta",),
        "aliases": (
            "llama-3.3-70b",
            "llama 3.3 70b",
            "llama 3.3 70b instruct",
            "meta/llama-3.3-70b-instruct",
        ),
    },
}
_GITHUB_CATALOG_CACHE: dict[str, Any] = {
    "token": None,
    "fetched_at": 0.0,
    "entries": (),
    "error": None,
}
_MODEL_ROUTE_FAILURE_CACHE: dict[str, dict[str, Any]] = {}
_MODEL_RUNTIME_CACHE: dict[tuple[str, str, str], dict[str, Any]] = {}
MODEL_RUNTIME_CACHE_TTL_SECONDS = 900
MODEL_RUNTIME_TEMP_FAILURE_TTL_SECONDS = 120
MODEL_RUNTIME_PROBE_TIMEOUT_SECONDS = 12


def env_secret(env_name: str) -> str | None:
    value = os.getenv(env_name, "").strip()
    if not value:
        return None
    if value.lower() in PLACEHOLDER_VALUES:
        return None
    return value


def _normalize_model_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _is_github_token(value: str | None) -> bool:
    return bool(value) and value.startswith(GITHUB_TOKEN_PREFIXES)


def github_models_enabled() -> bool:
    return os.getenv(ENABLE_GITHUB_MODELS_ENV, "false").strip().lower() == "true"


def github_models_api_key() -> str | None:
    if not github_models_enabled():
        return None
    explicit = env_secret(GITHUB_MODELS_API_KEY_ENV)
    if explicit:
        return explicit
    legacy = env_secret("OPENAI_API_KEY")
    if _is_github_token(legacy):
        return legacy
    return None


def _github_catalog_aliases(entry: dict[str, Any]) -> set[str]:
    aliases = {
        _normalize_model_key(str(entry.get("id") or "")),
        _normalize_model_key(str(entry.get("name") or "")),
    }
    publisher = str(entry.get("publisher") or "")
    name = str(entry.get("name") or "")
    if publisher and name:
        aliases.add(_normalize_model_key(f"{publisher} {name}"))
    return {alias for alias in aliases if alias}


def _fetch_github_catalog_entries(token: str) -> tuple[dict[str, Any], ...]:
    request = Request(
        GITHUB_MODELS_CATALOG_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": GITHUB_MODELS_API_VERSION,
            "User-Agent": "AI-Debate-Council/1.0",
        },
        method="GET",
    )
    with urlopen(request, timeout=6) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        return ()
    return tuple(item for item in payload if isinstance(item, dict))


def _catalog_error_reason(exc: Exception) -> str:
    text = str(exc)
    lower = text.lower()
    if "models permission is required" in lower or "models:read" in lower:
        return "GitHub Models rejected this token because it is missing `models:read`."
    if "401" in lower or "403" in lower:
        return "GitHub Models rejected this token during the catalog check."
    if "timed out" in lower or "timeout" in lower:
        return "GitHub Models did not answer the catalog check in time."
    return "GitHub Models catalog could not be checked right now."


def github_catalog_entries() -> tuple[dict[str, Any], ...]:
    token = github_models_api_key()
    if not token:
        return ()
    now = time.time()
    if (
        _GITHUB_CATALOG_CACHE["token"] == token
        and now - float(_GITHUB_CATALOG_CACHE["fetched_at"]) < GITHUB_MODELS_CACHE_TTL_SECONDS
    ):
        return _GITHUB_CATALOG_CACHE["entries"]
    try:
        entries = _fetch_github_catalog_entries(token)
        error = None
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        entries = ()
        error = _catalog_error_reason(exc)
    _GITHUB_CATALOG_CACHE.update(
        {"token": token, "fetched_at": now, "entries": entries, "error": error}
    )
    return entries


def github_catalog_error() -> str | None:
    token = github_models_api_key()
    if not token:
        return None
    github_catalog_entries()
    if _GITHUB_CATALOG_CACHE.get("token") != token:
        return None
    return _GITHUB_CATALOG_CACHE.get("error")


def github_catalog_id_for_model(model_name: str) -> str | None:
    candidates = github_catalog_ids_for_model(model_name)
    return candidates[0] if candidates else None


def _github_display_slug(name: str) -> str:
    base = re.sub(r"\(([^)]+)\)", r" \1 ", name)
    base = re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-")
    return re.sub(r"-{2,}", "-", base)


def github_catalog_ids_for_model(model_name: str) -> tuple[str, ...]:
    hints = GITHUB_MODEL_HINTS.get(model_name)
    token = github_models_api_key()
    if not token or not hints:
        return ()
    if github_model_route_is_blocked(model_name):
        return ()
    wanted_aliases = {
        _normalize_model_key(alias)
        for alias in (model_name, *hints.get("aliases", ()))
        if alias
    }
    wanted_publishers = {
        _normalize_model_key(publisher) for publisher in hints.get("publishers", ()) if publisher
    }
    for entry in github_catalog_entries():
        publisher = _normalize_model_key(str(entry.get("publisher") or ""))
        entry_id = str(entry.get("id") or "").strip()
        if not entry_id:
            continue
        if wanted_publishers and publisher and publisher not in wanted_publishers:
            continue
        if _github_catalog_aliases(entry) & wanted_aliases:
            candidate_ids: list[str] = [entry_id]
            publisher_name = str(entry.get("publisher") or "").strip()
            display_name = str(entry.get("name") or "").strip()
            if publisher_name and display_name:
                display_slug = _github_display_slug(display_name)
                for candidate in (
                    f"{publisher_name.lower()}/{display_slug}",
                    f"{publisher_name.lower()}/{display_slug.lower()}",
                    f"{publisher_name}/{display_slug}",
                ):
                    if candidate not in candidate_ids:
                        candidate_ids.append(candidate)
            return tuple(candidate_ids)
    return ()


def github_model_route_is_blocked(model_name: str) -> bool:
    model = MODEL_MAP.get(model_name)
    source = "unknown"
    token = ""
    if model is not None:
        direct_key = model.direct_api_key
        if direct_key:
            source = "provider"
            token = direct_key
        else:
            github_key = github_models_api_key()
            if github_key and GITHUB_MODEL_HINTS.get(model_name):
                source = "github_models"
                token = github_key
    cached = _MODEL_ROUTE_FAILURE_CACHE.get(model_name)
    if not cached:
        return False
    if cached.get("source") != source or cached.get("token") != token:
        _MODEL_ROUTE_FAILURE_CACHE.pop(model_name, None)
        return False
    if float(cached.get("expires_at", 0.0)) <= time.time():
        _MODEL_ROUTE_FAILURE_CACHE.pop(model_name, None)
        return False
    return True


def mark_model_unavailable(
    model_name: str,
    reason: str,
    *,
    ttl_seconds: int = GITHUB_ROUTE_FAILURE_TTL_SECONDS,
) -> None:
    model = MODEL_MAP.get(model_name)
    if model is None:
        return
    route = model.route
    if route is None:
        return
    _MODEL_ROUTE_FAILURE_CACHE[model_name] = {
        "token": route.api_key,
        "source": route.source,
        "reason": reason[:600],
        "expires_at": time.time() + ttl_seconds,
    }


def mark_github_model_unavailable(
    model_name: str,
    reason: str,
    *,
    ttl_seconds: int = GITHUB_ROUTE_FAILURE_TTL_SECONDS,
) -> None:
    mark_model_unavailable(model_name, reason, ttl_seconds=ttl_seconds)


def _runtime_cache_key(model: "SupportedModel", route: ModelRoute) -> tuple[str, str, str]:
    return (model.name, route.source, route.api_key)


def _cached_runtime_availability(model: "SupportedModel", route: ModelRoute) -> ModelAvailability | None:
    cached = _MODEL_RUNTIME_CACHE.get(_runtime_cache_key(model, route))
    if not cached:
        return None
    ttl = (
        MODEL_RUNTIME_CACHE_TTL_SECONDS
        if cached.get("available")
        else int(cached.get("ttl", MODEL_RUNTIME_TEMP_FAILURE_TTL_SECONDS))
    )
    checked_at = float(cached.get("checked_at", 0.0))
    if time.time() - checked_at > ttl:
        _MODEL_RUNTIME_CACHE.pop(_runtime_cache_key(model, route), None)
        return None
    return ModelAvailability(
        available=bool(cached.get("available")),
        reason=cached.get("reason"),
        checked_at=checked_at,
    )


def _store_runtime_availability(
    model: "SupportedModel",
    route: ModelRoute,
    availability: ModelAvailability,
    *,
    ttl_seconds: int,
) -> ModelAvailability:
    _MODEL_RUNTIME_CACHE[_runtime_cache_key(model, route)] = {
        "available": availability.available,
        "reason": availability.reason,
        "checked_at": availability.checked_at or time.time(),
        "ttl": ttl_seconds,
    }
    return availability


def _probe_error_reason(model: "SupportedModel", route: ModelRoute, error_text: str) -> tuple[str, int]:
    lower = error_text.lower()
    if route.source == "github_models" and (
        "unknown model" in lower or "model not found" in lower or "404" in lower
    ):
        return (
            "GitHub Models recognized the token, but its inference API rejected this model ID.",
            MODEL_RUNTIME_CACHE_TTL_SECONDS,
        )
    if "models permission is required" in lower or "models:read" in lower:
        return (
            "This GitHub token is missing GitHub Models permission (`models:read`).",
            MODEL_RUNTIME_CACHE_TTL_SECONDS,
        )
    if "authentication" in lower or "invalid api key" in lower or "incorrect api key" in lower:
        return (
            f"The API key for {model.provider_label} was rejected during a live check.",
            MODEL_RUNTIME_CACHE_TTL_SECONDS,
        )
    if "rate limit" in lower or "429" in lower:
        return (
            f"{model.provider_label} is rate limiting this model right now. Try again shortly.",
            MODEL_RUNTIME_TEMP_FAILURE_TTL_SECONDS,
        )
    if "overload" in lower or "overloaded" in lower or "529" in lower or "temporarily unavailable" in lower:
        return (
            f"{model.provider_label} is temporarily overloaded for this model right now.",
            MODEL_RUNTIME_TEMP_FAILURE_TTL_SECONDS,
        )
    if "timeout" in lower:
        return (
            f"{model.provider_label} did not answer the live model check in time.",
            MODEL_RUNTIME_TEMP_FAILURE_TTL_SECONDS,
        )
    if "not support" in lower or "unsupported" in lower:
        return (
            f"{model.provider_label} rejected this model for the current endpoint.",
            MODEL_RUNTIME_CACHE_TTL_SECONDS,
        )
    return (
        f"{model.provider_label} could not verify this model right now.",
        MODEL_RUNTIME_TEMP_FAILURE_TTL_SECONDS,
    )


async def verify_model_runtime(
    model: "SupportedModel", *, force_refresh: bool = False
) -> ModelAvailability:
    route = model.route
    if route is None:
        return ModelAvailability(
            available=False,
            reason=f"{model.api_key_env} is missing or no supported route is available.",
            checked_at=time.time(),
        )
    if model.provider == "mock":
        return ModelAvailability(available=True, checked_at=time.time())
    if not force_refresh:
        cached = _cached_runtime_availability(model, route)
        if cached is not None:
            return cached
    if acompletion is None:
        return _store_runtime_availability(
            model,
            route,
            ModelAvailability(
                available=False,
                reason="LiteLLM is unavailable, so live model verification could not run.",
                checked_at=time.time(),
            ),
            ttl_seconds=MODEL_RUNTIME_CACHE_TTL_SECONDS,
        )
    candidate_models = (route.litellm_model, *route.fallback_models)
    last_reason = f"{model.provider_label} could not verify this model right now."
    last_ttl = MODEL_RUNTIME_TEMP_FAILURE_TTL_SECONDS
    for candidate_model in candidate_models:
        try:
            await acompletion(
                model=candidate_model,
                messages=[{"role": "user", "content": "Reply with OK."}],
                api_key=route.api_key,
                stream=False,
                temperature=0.0,
                max_tokens=4,
                timeout=MODEL_RUNTIME_PROBE_TIMEOUT_SECONDS,
            )
            reason = None
            if route.source == "github_models" and candidate_model != route.litellm_model:
                reason = f"Verified through GitHub Models using fallback ID {candidate_model}."
            return _store_runtime_availability(
                model,
                route,
                ModelAvailability(available=True, reason=reason, checked_at=time.time()),
                ttl_seconds=MODEL_RUNTIME_CACHE_TTL_SECONDS,
            )
        except Exception as exc:
            reason, ttl_seconds = _probe_error_reason(model, route, str(exc))
            last_reason = reason
            last_ttl = ttl_seconds
            if route.source == "github_models" and "unknown model" in str(exc).lower():
                continue
            break
    if route.source == "github_models":
        mark_model_unavailable(model.name, last_reason, ttl_seconds=last_ttl)
    elif any(marker in last_reason.lower() for marker in ("rejected", "not available", "missing")):
        mark_model_unavailable(model.name, last_reason, ttl_seconds=last_ttl)
    return _store_runtime_availability(
        model,
        route,
        ModelAvailability(available=False, reason=last_reason, checked_at=time.time()),
        ttl_seconds=last_ttl,
    )


async def verify_models_runtime(models: list["SupportedModel"]) -> dict[str, ModelAvailability]:
    results = await asyncio.gather(*(verify_model_runtime(model) for model in models))
    return {model.name: result for model, result in zip(models, results, strict=False)}


@dataclass(frozen=True)
class ModelRoute:
    litellm_model: str
    api_key: str
    source: str
    fallback_models: tuple[str, ...] = ()


@dataclass(frozen=True)
class ModelAvailability:
    available: bool
    reason: str | None = None
    checked_at: float = 0.0


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
        return self.route is not None

    @property
    def runtime_available(self) -> bool:
        return self.route is not None

    @property
    def api_key(self) -> str | None:
        route = self.route
        return route.api_key if route else None

    @property
    def route(self) -> ModelRoute | None:
        if self.provider == "mock":
            if os.getenv(self.api_key_env, "false").strip().lower() == "true":
                return ModelRoute(self.litellm_model, "mock", "mock")
            return None
        if github_model_route_is_blocked(self.name):
            return None
        direct_key = self.direct_api_key
        if direct_key:
            return ModelRoute(self.litellm_model, direct_key, "provider")
        github_ids = github_catalog_ids_for_model(self.name)
        github_key = github_models_api_key()
        if github_ids and github_key:
            return ModelRoute(
                f"github/{github_ids[0]}",
                github_key,
                "github_models",
                fallback_models=tuple(f"github/{candidate}" for candidate in github_ids[1:]),
            )
        return None

    @property
    def direct_api_key(self) -> str | None:
        secret = env_secret(self.api_key_env)
        if self.provider == "openai" and _is_github_token(secret):
            return None
        return secret

    def public_dict(self, *, configured: bool | None = None) -> dict:
        payload = asdict(self)
        payload["configured"] = self.runtime_available if configured is None else configured
        payload["route_source"] = self.route.source if self.route else None
        if payload["route_source"] == "github_models":
            payload["api_key_env"] = GITHUB_MODELS_API_KEY_ENV
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
    models = [model for model in SUPPORTED_MODELS if model.runtime_available]
    openai_preferred_order = {"gpt-4o-mini": 0, "gpt-4o": 1, "gpt-5.4-mini": 2, "gpt-5.4-pro": 3}
    return sorted(
        models,
        key=lambda model: (
            PROVIDER_ORDER.index(model.provider) if model.provider in PROVIDER_ORDER else 999,
            openai_preferred_order.get(model.name, 100),
            model.name,
        ),
    )


def get_model(model_name: str) -> SupportedModel | None:
    return MODEL_MAP.get(model_name)


def get_available_model(model_name: str) -> SupportedModel | None:
    model = get_model(model_name)
    if model and model.runtime_available:
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
        unlocked_models = [model for model in provider_models if model.runtime_available]
        visible_models = unlocked_models if unlocked_only else provider_models
        direct_configured = any(model.direct_api_key for model in provider_models)
        github_configured = any(
            model.route is not None and model.route.source == "github_models"
            for model in provider_models
        )
        summaries.append(
            {
                "provider": provider,
                "provider_label": provider_models[0].provider_label,
                "api_key_env": (
                    provider_models[0].api_key_env
                    if direct_configured or not github_configured
                    else GITHUB_MODELS_API_KEY_ENV
                ),
                "configured": bool(unlocked_models),
                "unlocked_model_count": len(unlocked_models),
                "total_model_count": len(provider_models),
                "models": [model.public_dict() for model in visible_models],
            }
        )
    return summaries
