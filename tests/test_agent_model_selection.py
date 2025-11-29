import unittest

from core.agent import Agent


class DummyDB:
    def __init__(self):
        self.messages = []

    def add_message(self, *args, **kwargs):
        self.messages.append((args, kwargs))


class DummyApp:
    def __init__(self):
        self.available_models = []
        self.param_polish = False
        self.param_comments = False
        self.param_expert = False
        self.param_concise = False
        self.param_stackoverflow = False
        self.param_custom_text = ""
        self.param_auto_save_files = False
        self.use_google_search = False
        self.param_temperature = 0.0
        self.param_max_tokens = 1
        self.api_key = "test-key"
        self.model_priority_families = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]


class FakeModel:
    def __init__(self, name, methods):
        self.name = name
        self.supported_generation_methods = methods


class FakeGenAI:
    def __init__(self):
        self.configured_with = None

    def configure(self, api_key):
        self.configured_with = api_key

    def list_models(self):
        return [
            FakeModel("models/gemini-1.5-pro-001", ["generateContent"]),
            FakeModel("models/gemini-1.5-pro-latest", ["generateContent"]),
            FakeModel("models/gemini-1.5-flash-002", ["generateContent"]),
            FakeModel("models/embedding-something", ["embedText"]),
        ]


class AgentModelSelectionTests(unittest.TestCase):
    def setUp(self):
        self.app = DummyApp()
        self.db = DummyDB()
        self.genai = FakeGenAI()
        self.agent = Agent(self.db, self.app, genai_client=self.genai, image_loader=object())

    def test_select_latest_by_family_prefers_latest_suffix(self):
        family_latest = self.agent._select_latest_by_family(
            [
                "gemini-1.5-pro-001",
                "gemini-1.5-pro-latest",
                "gemini-1.5-flash-001",
                "gemini-1.5-flash-002",
            ]
        )
        self.assertEqual(family_latest["gemini-1.5-pro"], "gemini-1.5-pro-latest")
        self.assertEqual(family_latest["gemini-1.5-flash"], "gemini-1.5-flash-002")

    def test_choose_model_uses_priority_and_fallback(self):
        choice = self.agent._choose_model(
            {
                "gemini-1.5-flash": "gemini-1.5-flash-002",
                "other-family": "other-family-1",
            }
        )
        self.assertEqual(choice, "gemini-1.5-flash-002")
        fallback_choice = self.agent._choose_model({"other-family": "other-family-1"})
        self.assertEqual(fallback_choice, "other-family-1")

    def test_choose_model_fallback_prefers_alphabetical_family(self):
        choice = self.agent._choose_model(
            {
                "zzz-family": "a-variant",
                "aaa-family": "z-variant",
            }
        )
        self.assertEqual(choice, "z-variant")

    def test_discover_best_model_sets_cache_and_available_models(self):
        selected = self.agent.discover_best_model("secret")
        self.assertEqual(selected, "gemini-1.5-pro-latest")
        self.assertEqual(self.agent.cached_model, "gemini-1.5-pro-latest")
        self.assertEqual(self.app.available_models, [
            "gemini-1.5-flash-002",
            "gemini-1.5-pro-001",
            "gemini-1.5-pro-latest",
        ])
        self.assertEqual(self.genai.configured_with, "secret")

    def test_priority_override_respected(self):
        self.app.model_priority_families = ["experimental-alpha", "gemini-1.5-flash"]
        choice = self.agent._choose_model(
            {
                "gemini-1.5-flash": "gemini-1.5-flash-002",
                "experimental-alpha": "experimental-alpha-latest",
            }
        )
        self.assertEqual(choice, "experimental-alpha-latest")

    def test_priority_override_normalized(self):
        self.app.model_priority_families = [
            "  experimental-alpha  ",
            "gemini-1.5-flash",
            "gemini-1.5-flash",
            "",
        ]
        normalized = self.agent._priority_families()
        self.assertEqual(normalized, ["experimental-alpha", "gemini-1.5-flash"])


if __name__ == "__main__":
    unittest.main()
