"""Helpers for prompt formatting and text generation defaults."""

DEFAULT_CHAT_CONTEXT_LIMIT = 2048


def _normalize_messages(messages):
    """Normalize chat messages into the role/content shape models expect."""
    normalized = []

    for message in messages or []:
        if not isinstance(message, dict):
            continue

        role = str(message.get("role", "user")).strip().lower() or "user"
        if role not in {"system", "user", "assistant"}:
            role = "user"

        content = str(message.get("content", "")).strip()
        if not content:
            continue

        normalized.append({"role": role, "content": content})

    return normalized


def render_messages_for_model(tokenizer, messages):
    """Render a structured message list for the target tokenizer."""
    normalized = _normalize_messages(messages)
    if not normalized:
        return ""

    if hasattr(tokenizer, "apply_chat_template"):
        chat_template = getattr(tokenizer, "chat_template", None)
        if chat_template:
            try:
                return tokenizer.apply_chat_template(
                    normalized,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                pass

    parts = []
    for message in normalized:
        role = message["role"].capitalize()
        parts.append(f"{role}: {message['content']}")
    parts.append("Assistant:")
    return "\n\n".join(parts)


def prepare_generation_prompt(tokenizer, prompt):
    """Format a single prompt for chat-tuned tokenizers when possible."""
    return render_messages_for_model(
        tokenizer,
        [{"role": "user", "content": prompt}],
    )


def resolve_input_token_limit(tokenizer, requested_new_tokens, fallback_limit=DEFAULT_CHAT_CONTEXT_LIMIT):
    """Choose a sane prompt-token budget that does not collapse to output length."""
    model_limit = getattr(tokenizer, "model_max_length", None)
    if not isinstance(model_limit, int) or model_limit <= 0 or model_limit > 100000:
        model_limit = fallback_limit

    requested_new_tokens = max(32, int(requested_new_tokens or 0))
    reserved_for_prompt = max(fallback_limit, requested_new_tokens * 4)

    if model_limit <= requested_new_tokens:
        return max(256, model_limit)

    return max(256, min(model_limit - requested_new_tokens, reserved_for_prompt))


def looks_like_prompt_echo(text):
    """Detect responses that appear to repeat the hidden prompt instead of answering."""
    normalized = " ".join(str(text or "").split()).strip().lower()
    if not normalized:
        return False

    markers = (
        "jarvis runtime state:",
        "think planning notes for this turn:",
        "[inst]",
        "<<sys>>",
        "system you are jarvis",
        "system jarvis runtime state:",
        "i have the following files from your workspace",
        "please let me know what you would like to do with this information",
    )
    return any(marker in normalized for marker in markers)


def decode_generated_text(tokenizer, generated_ids, prompt_length):
    """Decode only the newly generated tokens when possible."""
    new_token_ids = generated_ids[prompt_length:]
    text = tokenizer.decode(new_token_ids, skip_special_tokens=True).strip()
    return text
