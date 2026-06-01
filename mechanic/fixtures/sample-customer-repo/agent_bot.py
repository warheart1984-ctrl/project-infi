"""Sample customer agent — intentional structural issues for mechanic fixtures."""

from __future__ import annotations

import openai


def run_invoice_agent(user_text: str) -> str:
    client = openai.OpenAI()
    first = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_text}],
    )
    second = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_text}],
    )
    return str(first.choices[0].message.content or "") + str(second.choices[0].message.content or "")
