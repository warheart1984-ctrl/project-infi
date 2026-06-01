from __future__ import annotations
import json
from openai import OpenAI
from app.config import OPENAI_API_KEY, OPENAI_MAIN_MODEL, OPENAI_FAST_MODEL
from app.tools import TOOL_SPECS

_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

SYSTEM_PROMPT = '''
You are Jarvis, a smart and concise AI assistant.
You can use tools when helpful.

Available tools:
{tool_specs}

Return ONLY valid JSON in one of these forms.

To use a tool:
{{"action":"tool","tool":"calculator","input":"2+2"}}

To answer normally:
{{"action":"final","response":"your response here"}}

Rules:
- Use tools for arithmetic, time, restricted Python execution, reading local files, listing local files, or lightweight web lookup.
- Prefer web_search for outside or current information.
- Do not invent tool results.
- Keep responses direct and practical.
'''.strip()

SUMMARY_PROMPT = '''
Summarize the most important durable context from this conversation.
Focus on user preferences, goals, projects, and notable results.
Keep it concise.
'''.strip()

RAG_PROMPT = '''
Answer the user's question using the provided document excerpts.
If the excerpts do not support the answer, say that clearly.

Question:
{question}

Excerpts:
{excerpts}
'''.strip()

def ensure_client() -> OpenAI:
    if _client is None:
        raise RuntimeError("OPENAI_API_KEY is missing. Add it to your .env file.")
    return _client

def chat(messages: list[dict[str, str]], temperature: float = 0.3, fast: bool = False) -> str:
    client = ensure_client()
    model = OPENAI_FAST_MODEL if fast else OPENAI_MAIN_MODEL
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""

def stream_chat(messages: list[dict[str, str]], temperature: float = 0.3):
    client = ensure_client()
    stream = client.chat.completions.create(
        model=OPENAI_MAIN_MODEL,
        messages=messages,
        temperature=temperature,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            yield delta

def summarize_messages(history: list[dict[str, str]]) -> str:
    if not history:
        return ""
    messages = [{"role": "system", "content": SUMMARY_PROMPT}] + history[-20:]
    return chat(messages, temperature=0.2, fast=True)

def answer_with_excerpts(question: str, excerpts: list[str]) -> str:
    prompt = RAG_PROMPT.format(
        question=question,
        excerpts="\n\n".join(f"- {e}" for e in excerpts) if excerpts else "- none"
    )
    return chat([{"role": "user", "content": prompt}], temperature=0.2, fast=False)

def make_system_prompt() -> str:
    return SYSTEM_PROMPT.format(tool_specs=json.dumps(TOOL_SPECS, indent=2))
