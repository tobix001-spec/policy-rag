"""Prompt templates and the structured output contract (PolicyAnswer.v1)."""
from __future__ import annotations

import json

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from policyrag.retrieval.retriever import Hit

SCHEMA_VERSION = "PolicyAnswer.v1"
ABSTAIN_TEXT = "I could not find this in the available documents."


class LLMAnswer(BaseModel):
    """What the model must return. Validated with Pydantic; failures count against format compliance."""

    answer: str = Field(description="Direct answer to the question, quoting numbers exactly as written in the context.")
    answerable: bool = Field(description="False if the context does not contain the answer.")
    sources: list[str] = Field(description="chunk_ids from the context that support the answer, e.g. 'policy-auto-classic-car#c2'.")
    confidence: float = Field(ge=0.0, le=1.0, description="Probability that the answer is correct and fully supported.")
    reasoning: str = Field(description="One short sentence on how the context supports the answer.")


ANSWER_JSON_SCHEMA = LLMAnswer.model_json_schema()

SYSTEM = f"""You are PolicyRAG, an assistant that answers questions for Velmora Assurance staff and customers \
using ONLY the provided document excerpts.

Rules:
1. Use only facts stated in the CONTEXT. Never use outside knowledge or guess.
2. Product names must match exactly. Information about "Bronze HMO" does not answer a question about "Bronze PPO". \
If the product asked about does not appear in the context, the question is not answerable.
3. If the context does not contain the answer, set "answerable" to false, set "answer" to "{ABSTAIN_TEXT}", \
and return an empty "sources" list.
4. When an amendment conflicts with an older document, the amendment wins; state the current value and its effective date.
5. Quote numbers, amounts and time periods exactly as written in the context.
6. For comparisons, the answer MUST state the value for each product, then which is higher or lower.
7. "sources" must list the chunk_ids (the text inside square brackets, without the brackets) of every excerpt you relied on.
8. "confidence" is a decimal between 0 and 1 (for example 0.9), never a percentage.
9. Respond with a single JSON object and nothing else.

Example of a valid response:
""" + (
    # literal braces doubled for ChatPromptTemplate (this part is deliberately NOT an f-string)
    '{{"answer": "Gold PPO has the lower deductible: $500 for Gold PPO versus $1,500 for Silver PPO.", '
    '"answerable": true, "sources": ["policy-health-gold-ppo#c1", "policy-health-silver-ppo#c1"], '
    '"confidence": 0.9, "reasoning": "Both deductibles are stated in the cost sharing sections."}}'
)

HUMAN = """CONTEXT:
{context}

QUESTION: {question}

Return JSON with keys: answer, answerable, sources, confidence, reasoning."""

ANSWER_PROMPT = ChatPromptTemplate.from_messages([("system", SYSTEM), ("human", HUMAN)])

REPAIR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You fix malformed JSON. Return only a JSON object that satisfies the schema."),
    ("human", "The following output failed validation.\n\nERROR: {error}\n\nOUTPUT:\n{output}\n\n"
              "SCHEMA:\n{schema}\n\nReturn the corrected JSON object only."),
])


def format_context(hits: list[Hit], superseded_by: dict[str, list[str]]) -> str:
    blocks = []
    for h in hits:
        c = h.chunk
        header = f"[{c['chunk_id']}] {c['title']} | {c['section']} | {c['doc_type']} | updated {c['last_updated']}"
        if c["doc_id"] in superseded_by:
            header += f" | NOTE: partly superseded by {', '.join(superseded_by[c['doc_id']])}"
        if c.get("supersedes"):
            header += f" | AMENDMENT to {c['supersedes']}"
        blocks.append(f"{header}\n{c['text']}")
    return "\n\n".join(blocks) if blocks else "(no documents retrieved)"


def schema_text() -> str:
    return json.dumps(ANSWER_JSON_SCHEMA)
