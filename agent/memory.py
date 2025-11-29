import os
import sqlite3
from threading import Lock
from typing import Iterable


class Memory:
    '''Prosta pamięć rozmów oparta o SQLite z lockiem pod użycie wielowątkowe.'''

    def __init__(self, db_path: str | None = None):
        self.db_path = self._resolve_db_path(db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.lock = Lock()
        self.default_history_limit = self._load_default_limit()
        self._history_cache: list[dict[str, str]] = []
        self._configure_connection()
        self._create_table()
        self._preload_cache()

    def _resolve_db_path(self, db_path: str | None) -> str:
        return db_path or os.getenv('DB_PATH', 'history.db')

    def _create_table(self) -> None:
        query = '''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        '''
        self._execute_write(query)

    def add_message(self, role: str, content: str) -> None:
        entry = {'role': role, 'content': content}

        with self.lock:
            self.conn.execute(
                'INSERT INTO messages (role, content) VALUES (?, ?)',
                (role, content),
            )
            self.conn.commit()
            self._history_cache.append(entry)

    def get_history(self, limit: int | None = None) -> list[dict]:
        resolved_limit = self._resolve_limit_value(limit)

        if resolved_limit == 0:
            return []

        with self.lock:
            if resolved_limit >= len(self._history_cache):
                return list(self._history_cache)

            start = len(self._history_cache) - resolved_limit
            return list(self._history_cache[start:])

    def clear(self) -> None:
        with self.lock:
            self.conn.execute('DELETE FROM messages')
            self.conn.commit()
            self._history_cache.clear()

    def set_default_limit(self, limit: int) -> None:
        self.default_history_limit = max(limit, 0)

    def close(self) -> None:
        with self.lock:
            try:
                self.conn.close()
            except Exception:
                pass

    def _execute_write(self, query: str, params: Iterable | None = None) -> sqlite3.Cursor:
        with self.lock:
            cursor = self.conn.execute(query, tuple(params or ()))
            self.conn.commit()
            return cursor

    def _preload_cache(self) -> None:
        with self.lock:
            cursor = self.conn.execute('SELECT role, content FROM messages ORDER BY id ASC')
            self._history_cache = [
                {'role': row[0], 'content': row[1]}
                for row in cursor.fetchall()
            ]

    def _configure_connection(self) -> None:
        with self.lock:
            self.conn.execute('PRAGMA journal_mode=WAL')
            self.conn.execute('PRAGMA synchronous=NORMAL')
            self.conn.commit()

    def _load_default_limit(self) -> int:
        try:
            env_limit = int(os.getenv('HISTORY_LIMIT', '50'))
        except ValueError:
            env_limit = 50

        return max(env_limit, 0)

    def _resolve_limit_value(self, limit: int | None) -> int:
        if limit is not None:
            return max(limit, 0)

        return self.default_history_limit
