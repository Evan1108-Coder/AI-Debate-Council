from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import math
import re
from typing import Any


SUPPORTED_CURRENCIES = ("USD", "CNY", "HKD", "EUR", "JPY", "GBP", "AUD", "CAD", "SGP")

# Fallback exchange rates relative to 1 USD. Kept local to avoid adding a fragile
# runtime currency dependency to the setup path.
EXCHANGE_RATES_PER_USD = {
    "USD": 1.0,
    "CNY": 7.25,
    "HKD": 7.8,
    "EUR": 0.92,
    "JPY": 155.0,
    "GBP": 0.79,
    "AUD": 1.52,
    "CAD": 1.36,
    "SGP": 1.35,
}

# Prices are USD per 1M input/output tokens for normal pay-as-you-go text use.
# Provider price pages change, so the UI labels these as estimates.
MODEL_PRICES_USD_PER_1M = {
    "gpt-5.4-pro": (30.0, 180.0),
    "gpt-5.4-mini": (0.75, 4.5),
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
    "claude-opus-4-6": (5.0, 25.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-3.5-sonnet": (3.0, 15.0),
    "gemini-3.1-pro": (2.0, 12.0),
    "gemini-3-flash": (0.5, 3.0),
    "gemini-2.5-flash-lite": (0.1, 0.4),
    "llama-4-maverick": (0.2, 0.6),
    "llama-4-scout": (0.11, 0.34),
    "llama-3.3-70b": (0.59, 0.79),
    "minimax-m2.7": (0.3, 1.2),
    "minimax-m2.5-lightning": (0.6, 2.4),
    "kimi-latest": (0.6, 2.0),
    "kimi-k2-thinking": (0.6, 2.0),
    "kimi-k2-turbo-preview": (0.6, 2.0),
    "kimi-k2.5-vision": (0.6, 2.0),
    "moonshot-v1-128k": (0.6, 2.0),
    "mock-debate-model": (0.0, 0.0),
}


@dataclass
class CostEntry:
    model: str
    input_tokens: int
    output_tokens: int
    input_usd_per_1m: float
    output_usd_per_1m: float
    cost_usd: float
    operation: str


class CostTracker:
    def __init__(self) -> None:
        self.entries: list[CostEntry] = []

    def record_call(
        self,
        *,
        model_name: str,
        input_text: str,
        output_text: str,
        operation: str,
    ) -> None:
        input_tokens = estimate_tokens(input_text)
        output_tokens = estimate_tokens(output_text)
        input_price, output_price = MODEL_PRICES_USD_PER_1M.get(model_name, (0.0, 0.0))
        cost_usd = (input_tokens * input_price + output_tokens * output_price) / 1_000_000
        self.entries.append(
            CostEntry(
                model=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                input_usd_per_1m=input_price,
                output_usd_per_1m=output_price,
                cost_usd=cost_usd,
                operation=operation,
            )
        )

    def summary(self, currency: str) -> dict[str, Any]:
        return self._summary_for_entries(self.entries, currency)

    def summary_since(self, start_index: int, currency: str) -> dict[str, Any]:
        return self._summary_for_entries(self.entries[max(0, start_index) :], currency)

    def _summary_for_entries(self, entries: list[CostEntry], currency: str) -> dict[str, Any]:
        normalized_currency = normalize_currency(currency)
        rate = EXCHANGE_RATES_PER_USD[normalized_currency]
        grouped: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "model": "",
                "input_tokens": 0,
                "output_tokens": 0,
                "calls": 0,
                "cost_usd": 0.0,
                "input_usd_per_1m": 0.0,
                "output_usd_per_1m": 0.0,
            }
        )
        for entry in entries:
            item = grouped[entry.model]
            item["model"] = entry.model
            item["input_tokens"] += entry.input_tokens
            item["output_tokens"] += entry.output_tokens
            item["calls"] += 1
            item["cost_usd"] += entry.cost_usd
            item["input_usd_per_1m"] = entry.input_usd_per_1m
            item["output_usd_per_1m"] = entry.output_usd_per_1m

        model_items = []
        for item in grouped.values():
            converted = item["cost_usd"] * rate
            model_items.append(
                {
                    **item,
                    "cost": round(converted, 8),
                    "cost_usd": round(item["cost_usd"], 8),
                }
            )
        model_items.sort(key=lambda item: item["cost_usd"], reverse=True)
        total_usd = sum(entry.cost_usd for entry in entries)
        return {
            "currency": normalized_currency,
            "total": round(total_usd * rate, 8),
            "total_usd": round(total_usd, 8),
            "input_tokens": sum(entry.input_tokens for entry in entries),
            "output_tokens": sum(entry.output_tokens for entry in entries),
            "calls": len(entries),
            "models": model_items,
            "estimated": True,
            "rate_source": "local fallback exchange rates",
        }


def normalize_currency(currency: str) -> str:
    cleaned = str(currency or "USD").upper().strip()
    return cleaned if cleaned in SUPPORTED_CURRENCIES else "USD"


def estimate_messages_tokens(messages: list[dict[str, str]]) -> int:
    return sum(estimate_tokens(message.get("content", "")) + 4 for message in messages)


def estimate_tokens(text: str) -> int:
    if not text or not text.strip():
        return 0
    cjk_chars = len(re.findall(r"[\u3400-\u9fff\uf900-\ufaff]", text))
    without_cjk = re.sub(r"[\u3400-\u9fff\uf900-\ufaff]", " ", text)
    wordish = len(re.findall(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", without_cjk))
    return max(1, math.ceil(cjk_chars * 1.6 + wordish * 1.3))


def message_input_text(messages: list[dict[str, str]]) -> str:
    return "\n".join(f"{message.get('role', 'user')}: {message.get('content', '')}" for message in messages)
