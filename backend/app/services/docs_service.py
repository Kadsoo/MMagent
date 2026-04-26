from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class DocsService:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def search(self, query: str, limit: int = 5) -> dict[str, Any]:
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("Search query cannot be empty.")

        query_terms = self._terms(clean_query)
        matches: list[dict[str, Any]] = []

        for path in self._document_files():
            text = path.read_text(encoding="utf-8")
            for chunk_index, chunk in enumerate(self._chunks(text)):
                score = self._score(chunk, clean_query, query_terms)
                if not score:
                    continue
                matches.append(
                    {
                        "file": str(path.relative_to(self.data_dir)),
                        "chunk": chunk_index,
                        "score": score,
                        "snippet": self._make_snippet(chunk, query_terms),
                    }
                )

        matches.sort(key=lambda item: item["score"], reverse=True)
        summary = (
            matches[0]["snippet"]
            if matches
            else "No exact keyword match. Try queries like runtime, tool calling, registry, RAG, or web search."
        )
        return {
            "query": clean_query,
            "summary": summary,
            "matches": matches[:limit],
            "source": "local-files",
            "retrieval_mode": "keyword-rag",
        }

    @staticmethod
    def _score(text: str, query: str, terms: list[str]) -> int:
        lowered = text.lower()
        score = sum(lowered.count(term) for term in terms)
        if not score and query.lower() in lowered:
            return 1
        return score

    @staticmethod
    def _terms(query: str) -> list[str]:
        lowered = query.lower()
        words = re.findall(r"[a-z0-9_]+", lowered)
        chinese_chars = re.findall(r"[\u4e00-\u9fff]", query)
        chinese_bigrams = [
            "".join(chinese_chars[index : index + 2])
            for index in range(max(len(chinese_chars) - 1, 0))
        ]
        return [term for term in [*words, *chinese_bigrams] if len(term) > 1]

    def _document_files(self) -> list[Path]:
        roots = [self.data_dir, self.data_dir / "docs"]
        files: list[Path] = []
        for root in roots:
            if not root.exists():
                continue
            files.extend(root.glob("*.md"))
            files.extend(root.glob("*.txt"))
        return sorted(set(files))

    @staticmethod
    def _chunks(text: str) -> list[str]:
        sections = re.split(r"\n(?=#{1,6}\s)", text)
        chunks: list[str] = []
        for section in sections:
            clean = section.strip()
            if not clean:
                continue
            paragraphs = [item.strip() for item in clean.split("\n\n") if item.strip()]
            if len(clean) <= 900:
                chunks.append(clean)
                continue
            chunks.extend(" ".join(paragraph.split()) for paragraph in paragraphs)
        return chunks

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
