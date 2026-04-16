import os
import unittest
from unittest.mock import patch

from backend.app.model_registry import MODEL_MAP, available_models, get_available_model


class ModelRegistryTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
