# RAG Design in MMagent

MMagent includes a lightweight RAG-style local knowledge base tool named
`search_docs`. It is implemented as a Tool Calling capability rather than as
hard-coded prompt text.

## Current RAG Flow

The current implementation is keyword-based RAG:

1. Non-sensitive Markdown and text documents are stored in backend/app/data/docs.
2. DocsService loads local `.md` and `.txt` files.
3. Documents are split into small chunks by headings and paragraphs.
4. The user query is converted into searchable terms.
5. Chunks are scored by keyword overlap.
6. The top matches are returned as tool results.
7. The Agent uses the retrieved snippets to produce the final answer.

Important files:

- backend/app/services/docs_service.py
- backend/app/tools/builtin.py
- backend/app/data/docs/

## Why It Is RAG

The Agent does not rely only on model memory. It retrieves external project
knowledge from local files, augments the model context with the retrieved
snippets through `tool_result`, and then generates an answer.

## What Is Not Included Yet

This is not yet vector RAG. It does not currently use embeddings, FAISS, Chroma,
Qdrant, reranking, or citation formatting. The architecture allows DocsService
to be upgraded later to an embedding-based vector store without changing the
Agent runtime or frontend trace visualization.
