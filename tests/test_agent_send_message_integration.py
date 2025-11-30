import os
import tempfile
import types
from unittest import mock, TestCase

from core.agent import Agent


class _FakeDB:
    def __init__(self, history):
        self._history = history
        self.messages = []

    def get_context_messages(self, session_id, limit):
        return list(self._history)

    def add_message(self, session_id, role, content):
        self.messages.append((role, content))


class _FakeChat:
    def __init__(self, recorder, response_text):
        self.recorder = recorder
        self.response_text = response_text

    def send_message(self, content_parts):
        self.recorder["content_parts"] = content_parts
        return types.SimpleNamespace(text=self.response_text)


class _FakeModel:
    def __init__(self, recorder, response_text):
        self.recorder = recorder
        self.response_text = response_text

    def start_chat(self, history):
        self.recorder["history"] = history
        return _FakeChat(self.recorder, self.response_text)


class _FakeGenAI:
    def __init__(self, response_text):
        self.configured_key = None
        self.model_kwargs = None
        self.response_text = response_text

    def configure(self, api_key):
        self.configured_key = api_key

    def GenerativeModel(self, **kwargs):  # pylint: disable=invalid-name
        self.model_kwargs = kwargs
        return _FakeModel(self.__dict__, self.response_text)


class AgentSendMessageIntegrationTests(TestCase):
    def setUp(self):
        self.app = types.SimpleNamespace(
            api_key="secret-key",
            param_auto_save_files=False,
            use_google_search=False,
            param_temperature=0.7,
            param_max_tokens=128,
            param_polish=False,
            param_comments=False,
            param_expert=False,
            param_concise=False,
            param_stackoverflow=False,
            param_custom_text="",
            open_web_preview=mock.Mock(),
        )

    def test_send_message_builds_payload_and_history(self):
        history = [
            {"role": "user", "content": "previous question"},
            {"role": "assistant", "content": "prior answer"},
        ]
        db = _FakeDB(history)
        fake_genai = _FakeGenAI("response text")

        agent = Agent(db_manager=db, app_instance=self.app, genai_client=fake_genai, image_loader=mock.Mock())

        callbacks = {"success": None, "error": None}

        def success_cb(text):
            callbacks["success"] = text

        def error_cb(text):
            callbacks["error"] = text

        user_message = "new question"
        files = {"main.py": "print('hi')"}

        with mock.patch("core.agent.Clock.schedule_once", lambda func, dt: func(0)):
            with mock.patch("core.agent.threading.Thread") as thread_cls:
                thread_cls.return_value = mock.Mock(start=lambda: thread_cls.call_args.kwargs["target"]())
                agent.send_message("session-1", user_message, files, images=None, callback_success=success_cb, callback_error=error_cb)

        self.assertEqual(callbacks["error"], None)
        self.assertEqual(callbacks["success"], "response text")

        self.assertEqual(fake_genai.configured_key, "secret-key")
        self.assertEqual(fake_genai.model_kwargs["model_name"], "models/gemini-1.5-pro")
        self.assertIn("Gemini Code Assist", fake_genai.model_kwargs["system_instruction"])

        expected_history = [
            {"role": "user", "parts": ["previous question"]},
        ]
        self.assertEqual(fake_genai.history, expected_history)

        expected_payload = "new question\n\n[CONTEXT FILES]:\n--- FILE: main.py ---\nprint('hi')\n"
        self.assertEqual(fake_genai.content_parts, [expected_payload])

        self.assertEqual(
            db.messages,
            [
                ("user", expected_payload),
                ("assistant", "response text"),
            ],
        )

        self.app.open_web_preview.assert_not_called()

    def test_send_message_enables_search_and_saves_html_preview(self):
        history = []
        db = _FakeDB(history)
        fake_genai = _FakeGenAI("ok ```html\n<html>hi</html>\n``` more")

        self.app.param_auto_save_files = True
        self.app.use_google_search = True

        agent = Agent(db_manager=db, app_instance=self.app, genai_client=fake_genai, image_loader=mock.Mock())

        callbacks = {"success": None, "error": None}

        def success_cb(text):
            callbacks["success"] = text

        def error_cb(text):
            callbacks["error"] = text

        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with mock.patch("core.agent.Clock.schedule_once", lambda func, dt: func(0)):
                    with mock.patch("core.agent.threading.Thread") as thread_cls:
                        thread_cls.return_value = mock.Mock(start=lambda: thread_cls.call_args.kwargs["target"]())
                        agent.send_message(
                            "session-2",
                            "ask",
                            file_contents=None,
                            images=None,
                            callback_success=success_cb,
                            callback_error=error_cb,
                        )
            finally:
                os.chdir(cwd)

            self.assertEqual(callbacks["error"], None)
            self.assertEqual(callbacks["success"], "ok ```html\n<html>hi</html>\n``` more")

            self.assertEqual(fake_genai.model_kwargs["tools"], [{"google_search_retrieval": {}}])

            preview_path = os.path.join(tmpdir, "preview", "index.html")
            self.assertTrue(os.path.exists(preview_path))
            with open(preview_path, "r", encoding="utf-8") as file_handle:
                self.assertEqual(file_handle.read(), "<html>hi</html>")

            self.app.open_web_preview.assert_called_once_with(os.path.join("preview", "index.html"))

    def test_send_message_appends_image_parts_and_db_marker(self):
        history = []
        db = _FakeDB(history)
        fake_genai = _FakeGenAI("response text")

        image_loader = mock.Mock()
        image_loader.open.side_effect = ["img-obj"]

        agent = Agent(db_manager=db, app_instance=self.app, genai_client=fake_genai, image_loader=image_loader)

        callbacks = {"success": None, "error": None}

        def success_cb(text):
            callbacks["success"] = text

        def error_cb(text):
            callbacks["error"] = text

        with mock.patch("core.agent.Clock.schedule_once", lambda func, dt: func(0)):
            with mock.patch("core.agent.threading.Thread") as thread_cls:
                thread_cls.return_value = mock.Mock(start=lambda: thread_cls.call_args.kwargs["target"]())
                agent.send_message(
                    "session-3",
                    "question",
                    file_contents=None,
                    images=["/tmp/image.png"],
                    callback_success=success_cb,
                    callback_error=error_cb,
                )

        self.assertEqual(callbacks["error"], None)
        self.assertEqual(callbacks["success"], "response text")

        image_loader.open.assert_called_once_with("/tmp/image.png")
        self.assertEqual(fake_genai.content_parts, ["question", "img-obj"])

        self.assertEqual(
            db.messages,
            [
                ("user", "question\n\n[ATTACHED 1 IMAGES]"),
                ("assistant", "response text"),
            ],
        )
