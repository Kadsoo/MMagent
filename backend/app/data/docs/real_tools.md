# Real Tool Services

MMagent implements common real tool services behind the Tool Registry.

## Weather

The `get_weather` tool can call Open-Meteo or OpenWeather. The tool hides
provider-specific API details from the Agent runtime.

## Web Search

The `web_search` tool performs internet lookup through DuckDuckGo Instant Answer
and an HTML search fallback. It is useful for common online information lookup.

## Todos

Todo tools are scoped by `user_id`. They use MySQL when configured and fall back
to a local JSON store for demos.

## Local Docs

The `search_docs` tool retrieves local knowledge base chunks. This is the
project's lightweight RAG entry point.
