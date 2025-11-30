# GitHub integration

DebugDruid can pull source files directly from GitHub repositories and attach them to the current chat session for context-aware prompts.

## Setup
- Optional: set `GITHUB_TOKEN` for authenticated access to private repositories or higher rate limits.
- Configure defaults in `config.json` (saved automatically from the UI) for:
  - `github_repo`: `owner/name` of the repository.
  - `github_branch`: branch or ref name (default `main`).
  - `github_files`: comma-separated list of file paths to download.
  - `github_token`: personal access token (if not using `GITHUB_TOKEN`).

## Usage
1. Open the right control panel and fill in the GitHub card fields.
2. Provide one or more file paths (comma-separated). Nested paths are supported.
3. Click **Pobierz z GitHub** to fetch and attach the files to the chat upload list.
4. Toggle the file checkboxes as usual before sending a message.

Files are stored under `github_cache/<owner_repo>/` and listed in the chat attachments panel for reuse.

**Safety note:** paths are normalized server-side (e.g., `..` or absolute prefixes are discarded) to avoid writing outside the cache
folder. Repository names must be in `owner/name` format with safe characters only. Branch names and paths are URL-encoded before
calling the GitHub API, and files must be base64-encoded and under 1 MB decoded size (default limit) to prevent unsafe or
unexpectedly large downloads. Use repository-relative paths such as `src/main.py`.
