import os
from typing import Any, Generator, Iterable, Mapping, Sequence

import ollama
from dotenv import load_dotenv

from agent.memory import Memory

ChatMessage = dict[str, str]
ChatChunk = Mapping[str, Any]
ChatStream = Iterable[ChatChunk]

load_dotenv()


class AgentService:
    '''Serwis agenta: spina LLM z pamięcią rozmów.'''

    def __init__(self, memory: Memory | None = None):
        self.model = os.getenv('MODEL_NAME', 'llama3')
        self.memory = memory or Memory()
        self.system_prompt = os.getenv('SYSTEM_PROMPT', '')

    def _build_messages(self) -> list[ChatMessage]:
        history = self.memory.get_history()
        messages: list[ChatMessage] = []

        if self.system_prompt:
            messages.append({
                'role': 'system',
                'content': self.system_prompt,
            })

        messages.extend(history)
        return messages

    def think_stream(self, user_text: str) -> Generator[str, None, None]:
        '''Zapisuje wiadomość użytkownika, woła Ollamę i streamuje odpowiedź.'''

        self._remember_user_message(user_text)
        messages = self._build_messages()

        try:
            collected_chunks: list[str] = []
            for chunk in self._response_chunks(messages):
                collected_chunks.append(chunk)
                yield chunk

            self._remember_assistant_message(''.join(collected_chunks))
        except Exception as e:
            yield f'[Błąd połączenia z modelem: {e}]'

    def _remember_user_message(self, content: str) -> None:
        self.memory.add_message('user', content)

    def _remember_assistant_message(self, content: str) -> None:
        if content.strip():
            self.memory.add_message('assistant', content)

    def _response_chunks(self, messages: Sequence[ChatMessage]) -> Generator[str, None, None]:
        for chunk in self._stream_model(messages):
            content = self._extract_chunk_content(chunk)
            if content:
                yield content

    def _stream_model(self, messages: Sequence[ChatMessage]) -> ChatStream:
        stream = self._create_model_stream(messages)
        return stream if isinstance(stream, Iterable) else ()

    def _create_model_stream(self, messages: Sequence[ChatMessage]) -> ChatStream:
        return ollama.chat(
            model=self.model,
            messages=messages,
            stream=True,
        )

    @staticmethod
    def _extract_chunk_content(chunk: Any) -> str:
        if not isinstance(chunk, Mapping):
            return ''

        message = chunk.get('message', {})
        if not isinstance(message, Mapping):
            return ''

        content = message.get('content', '')
        return content if isinstance(content, str) else ''
