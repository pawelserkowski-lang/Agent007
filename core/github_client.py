"""Lightweight GitHub fetcher for pulling repository files into context."""
from __future__ import annotations

import base64
import binascii
import json
import os
import urllib.error
import urllib.request
from urllib.parse import quote
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Dict, Iterable, Optional


class GitHubFetchError(RuntimeError):
    """Raised when GitHub content cannot be retrieved."""


@dataclass
class GitHubFetcher:
    token: Optional[str] = None
    user_agent: str = "DebugDruid/1.0"
    max_bytes: int = 1_000_000

    def fetch_files(self, repository: str, paths: Iterable[str], branch: str = "main") -> Dict[str, str]:
        """Return decoded contents for the requested repo paths.

        Parameters
        ----------
        repository: ``owner/name`` GitHub repository.
        paths: Iterable of file paths within the repository.
        branch: Branch or ref name; defaults to ``main``.
        """
        repo = sanitize_repository(repository)
        contents: Dict[str, str] = {}
        for path in paths:
            normalized = sanitize_repo_path(path)
            if not normalized:
                continue
            contents[normalized] = self._fetch_single(repo, normalized, branch)
        if not contents:
            raise GitHubFetchError("No valid paths requested")
        return contents

    def _fetch_single(self, repository: str, path: str, branch: str) -> str:
        request = self._build_request(repository, path, branch)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = response.read()
        except urllib.error.HTTPError as exc:  # pragma: no cover - network edge
            raise GitHubFetchError(f"HTTP {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover - network edge
            raise GitHubFetchError(str(exc.reason)) from exc

        try:
            data = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - unexpected payload
            raise GitHubFetchError("Invalid GitHub response") from exc

        if data.get("encoding") not in (None, "base64"):
            raise GitHubFetchError("Unsupported GitHub content encoding")

        if isinstance(data.get("size"), int) and data["size"] > self.max_bytes:
            raise GitHubFetchError("Requested file exceeds allowed size")

        encoded_content = data.get("content")
        if not encoded_content:
            raise GitHubFetchError("Missing content in GitHub response")

        if len(encoded_content) > self.max_bytes * 2:  # defensive against absent size field
            raise GitHubFetchError("Requested file exceeds allowed size")

        try:
            decoded_bytes = base64.b64decode(encoded_content, validate=True)
        except (binascii.Error, ValueError) as exc:  # pragma: no cover - corrupted data
            raise GitHubFetchError("Unable to decode GitHub content") from exc

        if len(decoded_bytes) > self.max_bytes:
            raise GitHubFetchError("Requested file exceeds allowed size")

        try:
            return decoded_bytes.decode("utf-8")
        except UnicodeDecodeError:  # pragma: no cover - fallback path
            return decoded_bytes.decode("utf-8", errors="replace")

    def _build_request(self, repository: str, path: str, branch: str) -> urllib.request.Request:
        encoded_path = quote(path, safe="/")
        encoded_branch = quote(branch, safe="")
        url = f"https://api.github.com/repos/{repository}/contents/{encoded_path}?ref={encoded_branch}"
        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": self.user_agent}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return urllib.request.Request(url, headers=headers)


def sanitize_repo_path(path: str) -> Optional[str]:
    """Normalize a repository-relative path and reject traversal attempts.

    Returns a POSIX-style relative path or ``None`` if the path is empty or
    escapes the repository root.
    """

    normalized = (path or "").strip().lstrip("/\\")
    if not normalized:
        return None

    posix_path = PurePosixPath(normalized)
    clean_path = os.path.normpath(posix_path.as_posix()).replace("\\", "/")
    if clean_path.startswith("..") or os.path.isabs(clean_path):
        return None
    return clean_path


def sanitize_repository(repository: str) -> str:
    """Validate ``owner/repo`` input to prevent path injection in requests."""

    normalized = (repository or "").strip()
    if not normalized:
        raise GitHubFetchError("Repository name is required")

    owner_repo = normalized.split("/")
    if len(owner_repo) != 2:
        raise GitHubFetchError("Repository must be in 'owner/name' format")

    owner, repo = owner_repo
    if not owner or not repo:
        raise GitHubFetchError("Repository must include both owner and name")

    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
    if not set(owner) <= allowed or not set(repo) <= allowed:
        raise GitHubFetchError("Repository contains invalid characters")

    return f"{owner}/{repo}"
