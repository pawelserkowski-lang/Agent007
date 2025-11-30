import base64
import json
import urllib.request
from unittest import TestCase, mock

from core.github_client import (
    GitHubFetcher,
    GitHubFetchError,
    sanitize_repo_path,
    sanitize_repository,
)


class DummyResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class GitHubFetcherTests(TestCase):
    def test_fetch_files_decodes_base64_content(self):
        encoded = base64.b64encode(b"hello world").decode("utf-8")
        payload = json.dumps({"content": encoded}).encode("utf-8")

        with mock.patch.object(urllib.request, "urlopen", return_value=DummyResponse(payload)):
            fetcher = GitHubFetcher()
            result = fetcher.fetch_files("octocat/Hello-World", ["README.md"], branch="main")

        self.assertEqual(result, {"README.md": "hello world"})

    def test_fetch_files_raises_on_missing_content(self):
        payload = json.dumps({"name": "file.txt"}).encode("utf-8")

        with mock.patch.object(urllib.request, "urlopen", return_value=DummyResponse(payload)):
            fetcher = GitHubFetcher()
            with self.assertRaises(GitHubFetchError):
                fetcher.fetch_files("octocat/Hello-World", ["README.md"], branch="main")

    def test_authorization_header_is_set_when_token_provided(self):
        encoded = base64.b64encode(b"abc").decode("utf-8")
        payload = json.dumps({"content": encoded}).encode("utf-8")
        captured_headers = {}

        def fake_urlopen(request, timeout=10):
            captured_headers["Authorization"] = request.get_header("Authorization")
            captured_headers["User-Agent"] = request.get_header("User-agent")
            return DummyResponse(payload)

        with mock.patch.object(urllib.request, "urlopen", side_effect=fake_urlopen):
            fetcher = GitHubFetcher(token="secret")
            fetcher.fetch_files("octocat/Hello-World", ["README.md"], branch="dev")

        self.assertEqual(captured_headers["Authorization"], "Bearer secret")
        self.assertEqual(captured_headers["User-Agent"], "DebugDruid/1.0")

    def test_empty_paths_raise_error(self):
        fetcher = GitHubFetcher()
        with self.assertRaises(GitHubFetchError):
            fetcher.fetch_files("octocat/Hello-World", [], branch="main")

    def test_rejects_non_base64_encoding(self):
        payload = json.dumps({"encoding": "gzip", "content": "abc"}).encode("utf-8")

        with mock.patch.object(urllib.request, "urlopen", return_value=DummyResponse(payload)):
            fetcher = GitHubFetcher()
            with self.assertRaises(GitHubFetchError):
                fetcher.fetch_files("octocat/Hello-World", ["README.md"], branch="main")

    def test_rejects_oversized_file_by_size_field(self):
        encoded = base64.b64encode(b"content").decode("utf-8")
        payload = json.dumps({"content": encoded, "size": 2_000_000}).encode("utf-8")

        with mock.patch.object(urllib.request, "urlopen", return_value=DummyResponse(payload)):
            fetcher = GitHubFetcher(max_bytes=1)
            with self.assertRaises(GitHubFetchError):
                fetcher.fetch_files("octocat/Hello-World", ["README.md"], branch="main")

    def test_rejects_oversized_file_by_encoded_length(self):
        encoded = "a" * 3_000_000
        payload = json.dumps({"content": encoded}).encode("utf-8")

        with mock.patch.object(urllib.request, "urlopen", return_value=DummyResponse(payload)):
            fetcher = GitHubFetcher(max_bytes=1)
            with self.assertRaises(GitHubFetchError):
                fetcher.fetch_files("octocat/Hello-World", ["README.md"], branch="main")

    def test_rejects_oversized_file_after_decoding(self):
        # Encoded length is below the defensive 2x limit but decoded bytes exceed max_bytes.
        content = b"x" * 6
        encoded = base64.b64encode(content).decode("utf-8")
        payload = json.dumps({"content": encoded}).encode("utf-8")

        with mock.patch.object(urllib.request, "urlopen", return_value=DummyResponse(payload)):
            fetcher = GitHubFetcher(max_bytes=5)
            with self.assertRaises(GitHubFetchError):
                fetcher.fetch_files("octocat/Hello-World", ["README.md"], branch="main")

    def test_sanitize_repo_path_rejects_traversal(self):
        self.assertIsNone(sanitize_repo_path("../secret.txt"))
        self.assertIsNone(sanitize_repo_path("/../secret.txt"))
        self.assertIsNone(sanitize_repo_path(""))

    def test_sanitize_repo_path_normalizes_segments(self):
        self.assertEqual(sanitize_repo_path("folder/../file.txt"), "file.txt")
        self.assertEqual(sanitize_repo_path("nested\\path/file.txt"), "nested/path/file.txt")

    def test_sanitize_repository_rejects_invalid_values(self):
        with self.assertRaises(GitHubFetchError):
            sanitize_repository("")
        with self.assertRaises(GitHubFetchError):
            sanitize_repository("owneronly")
        with self.assertRaises(GitHubFetchError):
            sanitize_repository("owner/na me")
        with self.assertRaises(GitHubFetchError):
            sanitize_repository("owner/na*me")

    def test_build_request_encodes_path_and_branch(self):
        fetcher = GitHubFetcher()
        request = fetcher._build_request("octocat/Hello-World", "docs/Read me.md", "feature/new branch")
        self.assertIn(
            "https://api.github.com/repos/octocat/Hello-World/contents/docs/Read%20me.md?ref=feature%2Fnew%20branch",
            request.full_url,
        )
