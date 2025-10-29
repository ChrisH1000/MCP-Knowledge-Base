"""Prompt templates for LLM-based answering."""

from rag_server.core.schemas import Match


def build_grounding_prompt(question: str, matches: list[Match]) -> str:
    """Build a grounded QA prompt from matches.

    Args:
        question: User question
        matches: Retrieved context matches

    Returns:
        Formatted prompt
    """
    # Build context from matches
    context_parts: list[str] = []
    for i, match in enumerate(matches, start=1):
        context_parts.append(
            f"[{i}] File: {match.path} (lines {match.start_line}-{match.end_line})\n"
            f"{match.snippet}\n"
        )

    context = "\n".join(context_parts)

    prompt = f"""You are a precise code assistant. Use ONLY the provided context to answer the question.
If you cannot answer based on the context, say "I don't have enough information to answer that."
Always include file:line citations in your answer.

User question:
{question}

Context (ranked snippets with file and line numbers):
{context}

Answer with a concise explanation. End with "Sources:" and list each citation as "- path:start_line-end_line".
"""

    return prompt
