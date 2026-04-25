from __future__ import annotations

from pathlib import Path
from typing import Any


class DocsService:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def search(self, query: str, limit: int = 5) -> dict[str, Any]:
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("Search query cannot be empty.")

        files = list(self.data_dir.glob("*.md")) + list(self.data_dir.glob("*.txt"))
        query_terms = [term.lower() for term in clean_query.split() if len(term) > 1]
        matches: list[dict[str, Any]] = []

        for path in files:
            text = path.read_text(encoding="utf-8")
            score = self._score(text, clean_query, query_terms)
            if not score:
                continue
            matches.append(
                {
                    "file": path.name,
                    "score": score,
                    "snippet": self._make_snippet(text, query_terms),
                }
            )

        matches.sort(key=lambda item: item["score"], reverse=True)
        summary = (
            matches[0]["snippet"]
            if matches
            else "No exact keyword match. Try queries like runtime, tool calling, registry, or game agent."
        )
        return {
            "query": clean_query,
            "summary": summary,
            "matches": matches[:limit],
            "source": "local-files",
        }

    @staticmethod
    def _score(text: str, query: str, terms: list[str]) -> int:
        lowered = text.lower()
        score = sum(lowered.count(term) for term in terms)
        if not score and query.lower() in lowered:
            return 1
        return score

    @staticmethod
    def _make_snippet(text: str, terms: list[str]) -> str:
        lowered = text.lower()
        index = 0
        for term in terms:
            index = lowered.find(term)
            if index >= 0:
                break
        start = max(index - 120, 0)
        end = min(index + 280, len(text))
        snippet = text[start:end].replace("\n", " ").strip()
        return " ".join(snippet.split())
