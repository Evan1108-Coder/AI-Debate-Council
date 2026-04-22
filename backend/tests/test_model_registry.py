import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch

from backend.app.model_registry import (
    MODEL_MAP,
    _GITHUB_CATALOG_CACHE,
    _MODEL_RUNTIME_CACHE,
    _MODEL_ROUTE_FAILURE_CACHE,
    available_models,
    get_available_model,
    github_catalog_id_for_model,
    github_catalog_ids_for_model,
    mark_github_model_unavailable,
    verify_model_runtime,
)


class ModelRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        _GITHUB_CATALOG_CACHE.update({"token": None, "fetched_at": 0.0, "entries": (), "error": None})
        _MODEL_ROUTE_FAILURE_CACHE.clear()
        _MODEL_RUNTIME_CACHE.clear()

    def test_model_map_knows_all_supported_models(self) -> None:
        self.assertEqual(len(MODEL_MAP), 21)
        self.assertEqual(MODEL_MAP["gpt-4o"].provider, "openai")
        self.assertEqual(MODEL_MAP["claude-sonnet-4-6"].provider, "anthropic")
        self.assertEqual(MODEL_MAP["llama-4-maverick"].provider, "groq")

    def test_one_provider_key_unlocks_all_models_for_that_provider(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            names = {model.name for model in available_models()}

        self.assertEqual(
            names,
            {"gpt-5.4-pro", "gpt-5.4-mini", "gpt-4o", "gpt-4o-mini"},
        )

    def test_multiple_provider_keys_unlock_combined_dropdown_models(self) -> None:
        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key"},
            clear=True,
        ):
            names = {model.name for model in available_models()}

        self.assertEqual(len(names), 8)
        self.assertIn("gpt-4o", names)
        self.assertIn("claude-opus-4-6", names)

    def test_locked_model_cannot_be_selected(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            self.assertIsNotNone(get_available_model("gpt-4o"))
            self.assertIsNone(get_available_model("claude-sonnet-4-6"))

    def test_blank_or_placeholder_key_does_not_unlock_provider(self) -> None:
        with patch.dict(
            os.environ,
            {"MOONSHOT_API_KEY": "   ", "MINIMAX_API_KEY": "your_minimax_key"},
            clear=True,
        ):
            names = {model.name for model in available_models()}

        self.assertNotIn("kimi-latest", names)
        self.assertNotIn("minimax-m2.7", names)

    @patch(
        "backend.app.model_registry._fetch_github_catalog_entries",
        return_value=(
            {"id": "openai/gpt-4o", "name": "OpenAI GPT-4o", "publisher": "OpenAI"},
            {"id": "openai/gpt-5.4", "name": "OpenAI GPT-5.4", "publisher": "OpenAI"},
            {"id": "google/gemini-3.1-pro", "name": "Gemini 3.1 Pro", "publisher": "Google"},
        ),
    )
    def test_github_models_api_key_unlocks_catalog_matched_models(self, _mock_fetch) -> None:
        with patch.dict(
            os.environ,
            {"ENABLE_GITHUB_MODELS": "true", "GITHUB_MODELS_API_KEY": "github_pat_test_value"},
            clear=True,
        ):
            names = [model.name for model in available_models()]

        self.assertEqual(names, ["gpt-4o", "gpt-5.4-pro", "gemini-3.1-pro"])

    @patch(
        "backend.app.model_registry._fetch_github_catalog_entries",
        return_value=(
            {"id": "openai/gpt-4o-mini", "name": "OpenAI GPT-4o mini", "publisher": "OpenAI"},
        ),
    )
    def test_legacy_github_token_in_openai_env_still_routes_through_catalog(self, _mock_fetch) -> None:
        with patch.dict(
            os.environ,
            {"ENABLE_GITHUB_MODELS": "true", "OPENAI_API_KEY": "github_pat_test_value"},
            clear=True,
        ):
            names = [model.name for model in available_models()]
            catalog_id = github_catalog_id_for_model("gpt-4o-mini")

        self.assertEqual(names, ["gpt-4o-mini"])
        self.assertEqual(catalog_id, "openai/gpt-4o-mini")

    @patch(
        "backend.app.model_registry._fetch_github_catalog_entries",
        return_value=(
            {
                "id": "meta/llama-4-maverick-17b-128e-instruct-fp8",
                "name": "Llama 4 Maverick (17B-128E-Instruct-FP8)",
                "publisher": "Meta",
            },
        ),
    )
    def test_github_unknown_model_failure_can_temporarily_hide_model(self, _mock_fetch) -> None:
        with patch.dict(
            os.environ,
            {"ENABLE_GITHUB_MODELS": "true", "GITHUB_MODELS_API_KEY": "github_pat_test_value"},
            clear=True,
        ):
            self.assertIn("llama-4-maverick", [model.name for model in available_models()])
            mark_github_model_unavailable("llama-4-maverick", "Unknown model")
            self.assertNotIn("llama-4-maverick", [model.name for model in available_models()])

    @patch(
        "backend.app.model_registry._fetch_github_catalog_entries",
        return_value=(
            {
                "id": "meta/llama-4-maverick-17b-128e-instruct-fp8",
                "name": "Llama 4 Maverick (17B-128E-Instruct-FP8)",
                "publisher": "Meta",
            },
        ),
    )
    def test_github_catalog_ids_include_display_name_fallbacks(self, _mock_fetch) -> None:
        with patch.dict(
            os.environ,
            {"ENABLE_GITHUB_MODELS": "true", "GITHUB_MODELS_API_KEY": "github_pat_test_value"},
            clear=True,
        ):
            ids = github_catalog_ids_for_model("llama-4-maverick")

        self.assertEqual(ids[0], "meta/llama-4-maverick-17b-128e-instruct-fp8")
        self.assertIn("meta/Llama-4-Maverick-17B-128E-Instruct-FP8", ids)

    @patch(
        "backend.app.model_registry._fetch_github_catalog_entries",
        return_value=(
            {
                "id": "meta/llama-4-maverick-17b-128e-instruct-fp8",
                "name": "Llama 4 Maverick (17B-128E-Instruct-FP8)",
                "publisher": "Meta",
            },
        ),
    )
    def test_verify_model_runtime_uses_github_fallback_id(self, _mock_fetch) -> None:
        response = {"choices": [{"message": {"content": "OK"}}]}
        completion = AsyncMock(
            side_effect=[
                RuntimeError("GithubException - Unknown model: meta/llama-4-maverick-17b-128e-instruct-fp8 | 400"),
                response,
            ]
        )
        with patch.dict(
            os.environ,
            {"ENABLE_GITHUB_MODELS": "true", "GITHUB_MODELS_API_KEY": "github_pat_test_value"},
            clear=True,
        ), patch("backend.app.model_registry.acompletion", completion):
            availability = asyncio.run(verify_model_runtime(MODEL_MAP["llama-4-maverick"]))

        self.assertTrue(availability.available)
        self.assertIn("fallback ID", availability.reason or "")

    @patch(
        "backend.app.model_registry._fetch_github_catalog_entries",
        return_value=(
            {
                "id": "meta/llama-4-maverick-17b-128e-instruct-fp8",
                "name": "Llama 4 Maverick (17B-128E-Instruct-FP8)",
                "publisher": "Meta",
            },
        ),
    )
    def test_verify_model_runtime_marks_github_unknown_model_unavailable(self, _mock_fetch) -> None:
        completion = AsyncMock(
            side_effect=RuntimeError(
                "GithubException - Unknown model: meta/llama-4-maverick-17b-128e-instruct-fp8 | 400"
            )
        )
        with patch.dict(
            os.environ,
            {"ENABLE_GITHUB_MODELS": "true", "GITHUB_MODELS_API_KEY": "github_pat_test_value"},
            clear=True,
        ), patch("backend.app.model_registry.acompletion", completion):
            availability = asyncio.run(verify_model_runtime(MODEL_MAP["llama-4-maverick"]))

        self.assertFalse(availability.available)
        self.assertIn("rejected this model ID", availability.reason or "")


if __name__ == "__main__":
    unittest.main()
