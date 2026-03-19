import json
from typing import Any

from app.modules.kb.retriever import RetrieverService


def build_kb_search_tool_definition() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "kb_search",
            "description": (
                "Search the documentation knowledge base for information relevant "
                "to the user's question. Returns matching text chunks with metadata."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The search query to find relevant documentation.",
                    },
                },
                "required": ["question"],
            },
        },
    }


async def execute_kb_search(
    retriever: RetrieverService,
    arguments: str,
    *,
    namespace: str = "default",
) -> str:
    args = json.loads(arguments)
    question: str = args["question"]

    contexts = await retriever.retrieve(question, namespace=namespace)

    if not contexts:
        return json.dumps({"confidence": 0.0, "namespace": namespace, "contexts": []})

    max_similarity = max(c.similarity for c in contexts)
    return json.dumps({
        "confidence": round(max_similarity, 2),
        "namespace": namespace,
        "contexts": [
            {
                "source": c.source,
                "chunk_index": c.chunk_index,
                "preview": c.content[:200],
                "full_text": c.content,
            }
            for c in contexts
        ],
    })
