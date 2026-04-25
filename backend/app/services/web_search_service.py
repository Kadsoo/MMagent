from __future__ import annotations

from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qs, unquote, urlencode, urlparse

import httpx


class WebSearchService:
    def __init__(self, base_url: str = "https://api.duckduckgo.com") -> None:
        self.base_url = base_url.rstrip("/")

    async def search(self, query: str, max_results: int = 5) -> dict[str, Any]:
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("Search query cannot be empty.")

        params = {
            "q": clean_query,
            "format": "json",
            "no_html": "1",
            "no_redirect": "1",
            "skip_disambig": "0",
        }
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            payload = await self._instant_answer(client, params)
            results = _extract_related_topics(payload, max_results=max_results)
            fallback_results: list[dict[str, str]] = []
            answer = (
                payload.get("Answer")
                or payload.get("AbstractText")
                or payload.get("Definition")
                or ""
            )
            if not answer and not results:
                fallback_results = await self._html_search(client, clean_query, max_results)
                results = fallback_results

        source_url = (
            payload.get("AbstractURL")
            or payload.get("DefinitionURL")
            or (results[0]["url"] if results else None)
        )
        return {
            "query": clean_query,
            "answer": answer,
            "heading": payload.get("Heading") or clean_query,
            "source_url": source_url,
            "results": results,
            "search_page_url": f"https://duckduckgo.com/?{urlencode({'q': clean_query})}",
            "note": (
                "DuckDuckGo Instant Answer API returns topic summaries and related "
                "answers. HTML fallback is used when no instant answer is available."
            ),
            "source": "DuckDuckGo Instant Answer API"
            if not fallback_results
            else "DuckDuckGo HTML Search",
        }

    async def _instant_answer(
        self,
        client: httpx.AsyncClient,
        params: dict[str, str],
    ) -> dict[str, Any]:
        try:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:240] if exc.response is not None else ""
            raise RuntimeError(
                f"Web search provider returned HTTP {exc.response.status_code}: {detail}"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Web search provider request failed: {exc.__class__.__name__}"
            ) from exc

    async def _html_search(
        self,
        client: httpx.AsyncClient,
        query: str,
        max_results: int,
    ) -> list[dict[str, str]]:
        try:
            response = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "MMagent/0.1 local demo"},
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return []

        parser = DuckDuckGoHtmlParser(max_results=max_results)
        parser.feed(response.text)
        return parser.results


def _extract_related_topics(payload: dict[str, Any], max_results: int) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []

    def walk(items: list[dict[str, Any]]) -> None:
        for item in items:
            if len(results) >= max_results:
                return
            nested = item.get("Topics")
            if isinstance(nested, list):
                walk(nested)
                continue
            text = item.get("Text")
            url = item.get("FirstURL")
            if text and url:
                results.append({"title": text.split(" - ")[0], "snippet": text, "url": url})

    related_topics = payload.get("RelatedTopics") or []
    if isinstance(related_topics, list):
        walk(related_topics)
    return results


class DuckDuckGoHtmlParser(HTMLParser):
    def __init__(self, max_results: int) -> None:
        super().__init__()
        self.max_results = max_results
        self.results: list[dict[str, str]] = []
        self._current: dict[str, str] | None = None
        self._capture_title = False
        self._capture_snippet = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if len(self.results) >= self.max_results:
            return

        attributes = {key: value or "" for key, value in attrs}
        class_name = attributes.get("class", "")
        if tag == "a" and "result__a" in class_name:
            self._finish_current()
            self._current = {
                "title": "",
                "snippet": "",
                "url": _clean_duckduckgo_url(attributes.get("href", "")),
            }
            self._capture_title = True
            return

        if self._current is not None and tag in {"a", "div"} and "result__snippet" in class_name:
            self._capture_snippet = True

    def handle_data(self, data: str) -> None:
        if self._current is None:
            return
        clean_data = " ".join(data.split())
        if not clean_data:
            return
        if self._capture_title:
            self._current["title"] = f"{self._current['title']} {clean_data}".strip()
        elif self._capture_snippet:
            self._current["snippet"] = f"{self._current['snippet']} {clean_data}".strip()

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._capture_title:
            self._capture_title = False
            return

        if self._capture_snippet and tag in {"a", "div"}:
            self._capture_snippet = False
            self._finish_current()

    def close(self) -> None:
        self._finish_current()
        super().close()

    def _finish_current(self) -> None:
        if (
            self._current
            and self._current.get("title")
            and self._current.get("url")
            and len(self.results) < self.max_results
        ):
            self.results.append(self._current)
        self._current = None


def _clean_duckduckgo_url(url: str) -> str:
    if not url:
        return url
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if "uddg" in query and query["uddg"]:
        return unquote(query["uddg"][0])
    return url
