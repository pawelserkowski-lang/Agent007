"""Architect-mode helpers for code auto-detection and response templating."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class DetectionResult:
    """Structured outcome of the lightweight detector."""

    language: str
    framework: str | None = None
    version: str | None = None

    def formatted(self) -> str:
        parts: list[str] = [self.language]
        if self.framework:
            parts.append(self.framework)
        if self.version:
            parts.append(self.version)
        return ", ".join(parts)


_KEYWORDS: Mapping[str, tuple[str, ...]] = {
    "Python": ("def ", "import ", "from ", "async def", "self", "print("),
    "JavaScript": ("function ", "export ", "export default", "const ", "let ", "=>", "console.log"),
    "TypeScript": ("interface ", "type ", "implements", ": number", ": string", "enum "),
    "C++": ("#include", "std::", "cout <<", "::iterator", "template<"),
    "C#": ("namespace ", "using ", "public class", "async Task", "private string"),
    "Java": ("public class", "System.out", "@Override", "implements", "extends"),
    "Go": ("package ", "func ", "import (", "fmt.", "make("),
    "PHP": ("<?php", "echo ", "->", "function ", "namespace "),
    "Ruby": ("def ", "class ", "module ", "puts ", "end"),
    "Rust": ("fn ", "let ", "use ", "crate", "::"),
    "SQL": ("SELECT ", "INSERT ", "UPDATE ", "DELETE ", "CREATE TABLE", "WHERE "),
    "HTML": ("<html", "<body", "<div", "<span", "<!DOCTYPE html"),
    "CSS": ("{", "color:", "margin:", "padding:", "display:"),
}

_FRAMEWORK_MARKERS: Mapping[str, Mapping[str, tuple[str, ...]]] = {
    "Python": {
        "FastAPI": ("fastapi", "from fastapi", "import fastapi"),
        "Flask": ("from flask", "import flask", "flask("),
        "Django": ("django", "from django", "import django"),
        "Kivy": ("kivy", "from kivy", "import kivy"),
    },
    "JavaScript": {
        "React": ("react", "from \"react\"", "from 'react'", "jsx"),
        "Next.js": ("next/router", "next/navigation", "from \"next\"", "from 'next'"),
        "Vue": ("vue", "from 'vue'", "from \"vue\""),
        "Express": ("express()", "require('express')", "from \"express\"", "from 'express'"),
    },
    "TypeScript": {
        "Angular": ("@angular", "angular/core"),
        "NestJS": ("@nestjs", "nestjs"),
    },
    "Go": {
        "Gin": ("gin.", "github.com/gin-gonic", "gin.Default"),
    },
    "PHP": {
        "Laravel": ("laravel", "Illuminate\\", "artisan"),
    },
    "Ruby": {
        "Rails": ("rails", "ActiveRecord", "ActionController", "Rails."),
    },
    "Rust": {
        "Actix": ("actix-web", "use actix", "actix::"),
        "Rocket": ("rocket::", "rocket::build", "use rocket"),
    },
}

_LOWER_KEYWORDS: Mapping[str, tuple[str, ...]] = {
    language: tuple(marker.lower() for marker in markers)
    for language, markers in _KEYWORDS.items()
}

_LOWER_FRAMEWORK_MARKERS: Mapping[str, Mapping[str, tuple[str, ...]]] = {
    language: {
        framework: tuple(marker.lower() for marker in markers)
        for framework, markers in frameworks.items()
    }
    for language, frameworks in _FRAMEWORK_MARKERS.items()
}

_VERSION_HINTS: Mapping[str, tuple[str, ...]] = {
    "Python": ("python", "py"),
    "JavaScript": ("node", "deno", "react", "next"),
    "TypeScript": ("typescript", "ts"),
    "C++": ("c++", "cpp"),
    "Go": ("go",),
    "PHP": ("php",),
    "Ruby": ("ruby", "rails"),
    "Rust": ("rust", "actix", "rocket"),
}

_SEMVER_PATTERN = re.compile(r"\b(\d+\.\d+(?:\.\d+)?)\b")
_VERSION_PATTERN_CACHE: dict[str, re.Pattern[str]] = {}


def detect_language(sample: str) -> DetectionResult:
    """Best-effort heuristic language, framework, and version detection.

    The helper prefers clear keyword matches and falls back to "Plaintext".
    This avoids external dependencies while giving architect-mode responses a
    consistent AUTO-DETEKCJA preface with richer context when possible.
    """

    lowered = sample.lower()
    language = _detect_language(lowered)
    framework = _detect_framework(language, lowered)
    version = _detect_version(language, framework, lowered)
    return DetectionResult(language=language, framework=framework, version=version)


def _detect_language(sample: str) -> str:
    best_language = "Plaintext"
    best_score = 0
    for language, markers in _LOWER_KEYWORDS.items():
        score = _match_score(sample, markers)
        if score > best_score:
            best_score = score
            best_language = language
    return best_language


def _detect_framework(language: str, sample: str) -> str | None:
    frameworks = _LOWER_FRAMEWORK_MARKERS.get(language)
    if not frameworks:
        return None

    best_framework: str | None = None
    best_score = 0
    for framework, markers in frameworks.items():
        score = _match_score(sample, markers)
        if score > best_score:
            best_score = score
            best_framework = framework
    return best_framework if best_score else None


def _detect_version(language: str, framework: str | None, sample: str) -> str | None:
    hints: list[str] = list(_VERSION_HINTS.get(language, ()))
    if framework:
        hints.append(framework)

    for hint in hints:
        version = _search_version(sample, hint)
        if version:
            return version
    match = _SEMVER_PATTERN.search(sample)
    return match.group(1) if match else None


def _search_version(sample: str, name: str) -> str | None:
    pattern = _VERSION_PATTERN_CACHE.get(name)
    if not pattern:
        pattern = re.compile(
            rf"{re.escape(name)}\s*(?:=|:)?\s*v?(\d+(?:\.\d+){{0,2}})",
            re.IGNORECASE,
        )
        _VERSION_PATTERN_CACHE[name] = pattern

    match = pattern.search(sample)
    return match.group(1) if match else None


def _match_score(sample: str, markers: Iterable[str]) -> int:
    return sum(sample.count(marker) for marker in markers)


def build_architect_response(code: str) -> str:
    """Render the architect-mode template populated with auto-detection."""

    detection = detect_language(code)
    return (
        f"AUTO-DETEKCJA: {detection.formatted()}\n\n"
        "DIAGNOZA:\n"
        "- 🐛 ...\n"
        "- 🛡️ ...\n"
        "- 👴 ...\n\n"
        "MODERNIZACJA I NAPRAWA (Finalny Kod):\n"
        "" + code.strip() + "\n"
    )
