import threading

from kivy.lang import Builder
from kivy.clock import Clock, mainthread
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from agent.brain import AgentService
from ui.widgets import ChatBubble


class MainScreen(MDScreen):
    '''Główny ekran czatu z lokalnym agentem AI.'''

    def __init__(self, agent, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent
        self.thinking = False
        self.current_ai_bubble = None
        self.last_user_message = ''
        self.preview_error = False

        # historia ładowana po zbudowaniu KV
        Clock.schedule_once(self.load_history, 0)

    def on_kv_post(self, base_widget):
        self._prefill_settings()
        self._refresh_preview_metadata()
        self._set_preview_idle(force=True)

    def load_history(self, dt):
        try:
            limit = self._get_history_limit()
            history = self.agent.memory.get_history(limit=limit)
            for msg in history:
                role = msg.get('role')
                if role == 'system':
                    continue
                content = msg.get('content', '')
                is_user = role == 'user'
                self.add_bubble(content, is_user, scroll=False)
            self.scroll_to_bottom()
        except Exception as e:
            print(f'Błąd ładowania historii: {e}')
        else:
            self._set_preview_idle(force=True)

    def refresh_history(self):
        self._apply_history_limit_from_input()
        self._clear_chat_view()
        self.load_history(0)

    def clear_history(self):
        if self.thinking:
            return
        try:
            self.agent.memory.clear()
            self._clear_chat_view()
        except Exception as e:
            print(f'Błąd czyszczenia historii: {e}')

    def apply_system_prompt(self):
        self.agent.system_prompt = self.ids.system_prompt_input.text

    def apply_history_limit(self):
        self._apply_history_limit_from_input()
        self.refresh_history()

    def apply_model(self):
        new_model = self.ids.model_input.text.strip()
        if new_model:
            self.agent.model = new_model
            self._refresh_preview_metadata()

    def send_message(self):
        if self.thinking:
            return

        text = self.ids.user_input.text.strip()
        if not text:
            return

        self._apply_history_limit_from_input()
        self.ids.user_input.text = ''
        self.last_user_message = text
        self.add_bubble(text, is_user=True)
        self.thinking = True
        self.ids.loading_spinner.active = True
        self._set_preview_active(text)

        thread = threading.Thread(
            target=self._run_agent_task,
            args=(text,),
            daemon=True,
        )
        thread.start()

    def _run_agent_task(self, text: str):
        # przygotuj placeholder na odpowiedź AI
        self.create_ai_bubble_placeholder()
        try:
            stream = self.agent.think_stream(text)
            full_text = ''
            for chunk in stream:
                full_text += chunk
                self.update_ai_bubble(full_text)
        except Exception as e:
            self.update_ai_bubble(f'Error: {e}')
            self._set_preview_error(str(e))
        finally:
            self.finish_agent_task()

    @mainthread
    def add_bubble(self, text: str, is_user: bool, scroll: bool = True):
        bubble = ChatBubble(text=text, is_user=is_user)
        self.ids.chat_list.add_widget(bubble)
        if scroll:
            self.scroll_to_bottom()

    @mainthread
    def create_ai_bubble_placeholder(self):
        self.current_ai_bubble = ChatBubble(text='...', is_user=False)
        self.ids.chat_list.add_widget(self.current_ai_bubble)
        self.scroll_to_bottom()

    @mainthread
    def update_ai_bubble(self, text: str):
        if self.current_ai_bubble is not None:
            self.current_ai_bubble.update_text(text)
            self.scroll_to_bottom()
        self._update_preview_stream(text)

    @mainthread
    def finish_agent_task(self):
        self.thinking = False
        self.ids.loading_spinner.active = False
        self.current_ai_bubble = None
        if not self.preview_error:
            self._set_preview_idle()

    @mainthread
    def scroll_to_bottom(self):
        # przewiń na dół po następnym cyklu, gdy layout się przeliczy
        def _scroll(_dt):
            self.ids.scroll_view.scroll_y = 0
        Clock.schedule_once(_scroll, 0)

    def _clear_chat_view(self) -> None:
        self.ids.chat_list.clear_widgets()
        self.current_ai_bubble = None

    def _prefill_settings(self) -> None:
        self.ids.model_input.text = self.agent.model
        self.ids.system_prompt_input.text = self.agent.system_prompt
        self.ids.history_limit_input.text = str(
            self.agent.memory.default_history_limit)

    def _get_history_limit(self) -> int:
        raw_limit = self.ids.history_limit_input.text.strip()
        try:
            return max(int(raw_limit), 0)
        except ValueError:
            return self.agent.memory.default_history_limit

    def _apply_history_limit_from_input(self) -> None:
        limit = self._get_history_limit()
        self.agent.memory.set_default_limit(limit)
        self._refresh_preview_metadata()

    @mainthread
    def _set_preview_active(self, prompt: str) -> None:
        self.preview_error = False
        self.ids.preview_status.text = 'Agent analizuje wiadomość'
        self.ids.preview_status.text_color = 0.58, 0.82, 1, 1
        self.ids.preview_spinner.active = True
        self.ids.preview_prompt.text = f'„{self._trim_preview(prompt)}”'
        self.ids.preview_stream.text = 'Rozpoczynanie generowania...'

    @mainthread
    def _set_preview_error(self, message: str) -> None:
        self.preview_error = True
        self.ids.preview_status.text = 'Błąd odpowiedzi'
        self.ids.preview_status.text_color = 1, 0.54, 0.5, 1
        self.ids.preview_spinner.active = False
        self.ids.preview_stream.text = self._trim_preview(message)

    @mainthread
    def _set_preview_idle(self, force: bool = False) -> None:
        if self.preview_error and not force:
            return
        self.preview_error = False
        self.ids.preview_status.text = 'Gotowy do pracy'
        self.ids.preview_status.text_color = 0.58, 0.82, 1, 1
        self.ids.preview_spinner.active = False
        if self.last_user_message:
            self.ids.preview_prompt.text = f'„{self._trim_preview(self.last_user_message)}”'
        self.ids.preview_stream.text = 'Czekam na nowe polecenie...'
        self._refresh_preview_metadata()

    @mainthread
    def _refresh_preview_metadata(self) -> None:
        self.ids.preview_model.text = f'Model: {self.agent.model or "—"}'
        self.ids.preview_history.text = (
            f'Historia: {self.agent.memory.default_history_limit} ostatnich wpisów')

    @mainthread
    def _update_preview_stream(self, text: str) -> None:
        if self.ids.preview_spinner.active:
            self.ids.preview_status.text = 'Strumieniuję odpowiedź'
        self.ids.preview_stream.text = self._trim_preview(text)

    def _trim_preview(self, text: str, limit: int = 180) -> str:
        clean_text = text.strip()
        return (clean_text[:limit] + '…') if len(clean_text) > limit else clean_text


class LocalAIAgentApp(MDApp):
    def build(self):
        self.title = 'Local AI Agent (KivyMD + Ollama)'
        self.theme_cls.primary_palette = 'LightBlue'
        self.theme_cls.theme_style = 'Light'

        Builder.load_file('ui/layout.kv')

        self.agent = AgentService()
        return MainScreen(agent=self.agent)

    def on_stop(self):
        # grzecznie zamknij połączenie z bazą
        memory = getattr(self.agent, 'memory', None)
        if memory is not None:
            try:
                memory.close()
            except Exception as e:
                print(f'Błąd zamykania bazy: {e}')


if __name__ == '__main__':
    LocalAIAgentApp().run()
